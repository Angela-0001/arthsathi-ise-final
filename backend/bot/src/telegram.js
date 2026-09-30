import { Bot } from "grammy";
import axios from "axios";
import FormData from "form-data";
import { sendToBackend } from "./gateway.js";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

const WELCOME = `🙏 नमस्ते! ArthSathi में आपका स्वागत है।\n\nHello! I'm ArthSathi. Type:\n1️⃣ *1* — Government Schemes\n2️⃣ *2* — Financial Roadmap\n3️⃣ *3* — Analyze a Document\n\nOr send a photo/PDF of any document to check for risky clauses.`;

export function startTelegramBot() {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  if (!token) {
    console.log("[Telegram] No BOT_TOKEN set. Skipping.");
    return;
  }

  const bot = new Bot(token);

  // /start
  bot.command("start", (ctx) => ctx.reply(WELCOME, { parse_mode: "Markdown" }));

  // /schemes
  bot.command("schemes", async (ctx) => {
    await ctx.reply("⏳ Fetching eligible schemes...");
    const result = await sendToBackend({
      user_id: String(ctx.from.id),
      channel: "telegram",
      intent: "scheme_match",
      detected_language: "hi",
    });
    await ctx.reply(result.text_response || "No schemes found. Please complete your profile on the web app first.");
  });

  // /roadmap
  bot.command("roadmap", async (ctx) => {
    await ctx.reply("⏳ Building your financial roadmap...");
    const result = await sendToBackend({
      user_id: String(ctx.from.id),
      channel: "telegram",
      intent: "financial_roadmap",
      detected_language: "hi",
    });
    await ctx.reply(result.text_response || "Could not generate roadmap. Please complete your profile first.");
  });

  // Voice note
  bot.on("message:voice", async (ctx) => {
    await ctx.reply("🎙️ Processing your voice message...");
    const file = await ctx.getFile();
    const audio_url = `https://api.telegram.org/file/bot${token}/${file.file_path}`;
    const result = await sendToBackend({
      user_id: String(ctx.from.id),
      channel: "telegram",
      audio_url,
      detected_language: "hi",
    });
    await ctx.reply(result.text_response || "Sorry, could not process audio.");
  });

  // Photo or document file → risk analysis
  bot.on(["message:photo", "message:document"], async (ctx) => {
    await ctx.reply("📄 Analyzing document for risky clauses...");
    try {
      let fileId, contentType, filename;

      if (ctx.message.photo) {
        fileId = ctx.message.photo[ctx.message.photo.length - 1].file_id;
        contentType = "image/jpeg";
        filename = "photo.jpg";
      } else {
        fileId = ctx.message.document.file_id;
        const mime = ctx.message.document.mime_type || "image/jpeg";
        contentType = mime;
        filename = ctx.message.document.file_name || "document";
      }

      // Get file download URL via Telegram API
      const fileInfoResp = await axios.get(
        `https://api.telegram.org/bot${token}/getFile?file_id=${fileId}`,
        { timeout: 10000 }
      );
      const filePath = fileInfoResp.data.result.file_path;
      const fileUrl = `https://api.telegram.org/file/bot${token}/${filePath}`;

      // Download the file as buffer
      const downloadResp = await axios.get(fileUrl, {
        responseType: "arraybuffer",
        timeout: 20000,
      });
      const fileBuffer = Buffer.from(downloadResp.data);

      // POST multipart to backend
      const form = new FormData();
      form.append("file", fileBuffer, { filename, contentType });

      const resp = await axios.post(
        `${BACKEND_URL}/documents/analyze?lang=hi`,
        form,
        { headers: form.getHeaders(), timeout: 60000 }
      );

      const data = resp.data;
      const flags = data.risk_flags || [];
      const high = flags.filter(f => f.risk_level === "high").length;
      const medium = flags.filter(f => f.risk_level === "medium").length;
      const low = flags.filter(f => f.risk_level === "low").length;

      let reply = `📋 *Analysis Summary*\n${data.summary}\n`;
      reply += `\n🔴 High: ${high}  🟡 Medium: ${medium}  🔵 Low: ${low}\n`;

      if (flags.length > 0) {
        reply += `\n*Detected Clauses:*\n`;
        flags.slice(0, 6).forEach(f => {
          const emoji = f.risk_level === "high" ? "🔴" : f.risk_level === "medium" ? "🟡" : "🔵";
          reply += `\n${emoji} *${f.risk_level.toUpperCase()}*\n_${f.clause_text}_\n${f.explanation}\n`;
        });
      } else {
        reply += "\n✅ No risky clauses detected.";
      }

      await ctx.reply(reply, { parse_mode: "Markdown" });

    } catch (err) {
      console.error("[Telegram] Document error:", err.response?.data || err.message);
      await ctx.reply("❌ Could not analyze document. Please send a clearer image or try a PDF.");
    }
  });

  // Plain text — number shortcuts + general
  bot.on("message:text", async (ctx) => {
    const text = ctx.message.text.trim();

    if (text === "1") {
      ctx.message.text = "/schemes";
      await ctx.reply("⏳ Fetching eligible schemes...");
      const result = await sendToBackend({
        user_id: String(ctx.from.id),
        channel: "telegram",
        intent: "scheme_match",
        detected_language: "hi",
      });
      return ctx.reply(result.text_response || "No schemes found. Complete your profile on the web app first.");
    }

    if (text === "2") {
      await ctx.reply("⏳ Building your financial roadmap...");
      const result = await sendToBackend({
        user_id: String(ctx.from.id),
        channel: "telegram",
        intent: "financial_roadmap",
        detected_language: "hi",
      });
      return ctx.reply(result.text_response || "Could not generate roadmap.");
    }

    if (text === "3") {
      return ctx.reply("📸 Please send a photo or PDF of the document you want to analyze.");
    }

    // General message
    const result = await sendToBackend({
      user_id: String(ctx.from.id),
      channel: "telegram",
      raw_text: text,
      detected_language: "hi",
    });
    await ctx.reply(result.text_response || WELCOME, { parse_mode: "Markdown" });
  });

  bot.catch((err) => console.error("[Telegram] Error:", err));
  bot.start();
  console.log("[Telegram] Bot started");
}
