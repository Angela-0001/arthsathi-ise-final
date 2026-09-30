import { Bot, InputFile } from "grammy";
import axios from "axios";
import FormData from "form-data";
import { sendToBackend } from "./gateway.js";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export function startTelegramBot() {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  if (!token) {
    console.log("[Telegram] No BOT_TOKEN set. Skipping.");
    return;
  }

  const bot = new Bot(token);

  bot.command("start", (ctx) =>
    ctx.reply(
      "🙏 नमस्ते! मैं ArthSathi हूँ।\n\n" +
      "मैं आपकी मदद कर सकता हूँ:\n" +
      "📋 /schemes — योग्य सरकारी योजनाएँ\n" +
      "🗺️ /roadmap — वित्तीय रोडमैप\n" +
      "📄 दस्तावेज़ की फ़ोटो भेजें — जाँच के लिए\n\n" +
      "Hello! Send me a message, voice note, or document photo."
    )
  );

  bot.command("schemes", async (ctx) => {
    await ctx.reply("Fetching eligible schemes...");
    const result = await sendToBackend({
      user_id: String(ctx.from.id),
      channel: "telegram",
      intent: "scheme_match",
      detected_language: "hi",
    });
    await ctx.reply(result.text_response || "No schemes found. Please complete your profile first.");
  });

  bot.command("roadmap", async (ctx) => {
    await ctx.reply("Building your financial roadmap...");
    const result = await sendToBackend({
      user_id: String(ctx.from.id),
      channel: "telegram",
      intent: "financial_roadmap",
      detected_language: "hi",
    });
    await ctx.reply(result.text_response || "Could not generate roadmap.");
  });

  // Voice note → ASR → backend
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

  // Photo/document → document risk analysis
  bot.on(["message:photo", "message:document"], async (ctx) => {
    await ctx.reply("📄 Analyzing document for risky clauses...");
    try {
      let fileId;
      let fileName = "document.jpg";
      let contentType = "image/jpeg";

      if (ctx.message.photo) {
        fileId = ctx.message.photo[ctx.message.photo.length - 1].file_id;
      } else {
        fileId = ctx.message.document.file_id;
        fileName = ctx.message.document.file_name || "document";
        contentType = ctx.message.document.mime_type || "image/jpeg";
      }

      const fileResp = await axios.get(
        `https://api.telegram.org/bot${token}/getFile?file_id=${fileId}`
      );
      const filePath = fileResp.data.result.file_path;
      const fileUrl = `https://api.telegram.org/file/bot${token}/${filePath}`;

      const imgResp = await axios.get(fileUrl, { responseType: "arraybuffer" });
      const fileBuffer = Buffer.from(imgResp.data);

      const form = new FormData();
      form.append("file", fileBuffer, { filename: fileName, contentType });

      const resp = await axios.post(
        `${BACKEND_URL}/documents/analyze?lang=hi`,
        form,
        { headers: form.getHeaders(), timeout: 60000 }
      );

      const data = resp.data;
      const flags = data.risk_flags || [];

      let reply = `📋 *Summary*\n${data.summary}\n`;
      if (flags.length > 0) {
        reply += `\n⚠️ *${flags.length} Risk Clause(s) Found:*\n`;
        flags.slice(0, 5).forEach(f => {
          const emoji = f.risk_level === "high" ? "🔴" : f.risk_level === "medium" ? "🟡" : "🔵";
          reply += `${emoji} *${f.risk_level.toUpperCase()}*: ${f.explanation}\n`;
        });
      } else {
        reply += "\n✅ No risky clauses detected.";
      }

      await ctx.reply(reply, { parse_mode: "Markdown" });
    } catch (err) {
      console.error("[Telegram] Document error:", err.response?.data || err.message);
      await ctx.reply("Could not analyze document. Please try a clearer image or a different file.");
    }
  });

  // Plain text
  bot.on("message:text", async (ctx) => {
    const result = await sendToBackend({
      user_id: String(ctx.from.id),
      channel: "telegram",
      raw_text: ctx.message.text,
      detected_language: "hi",
    });
    await ctx.reply(result.text_response || "Sorry, I didn't understand that.");
  });

  bot.catch((err) => console.error("[Telegram] Error:", err));
  bot.start();
  console.log("[Telegram] Bot started");
}
