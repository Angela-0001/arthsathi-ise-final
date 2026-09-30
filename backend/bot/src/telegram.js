import { Bot } from "grammy";
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

  // ── Commands ──────────────────────────────────────────────────────────────

  bot.command("start", (ctx) =>
    ctx.reply(
      "🙏 *नमस्ते! मैं ArthSathi हूँ।*\n\n" +
      "Hello! I'm ArthSathi — your financial companion.\n\n" +
      "*Commands:*\n" +
      "📋 /schemes — Eligible government schemes\n" +
      "🗺️ /roadmap — Financial roadmap\n" +
      "📄 /summary — Summary of last document\n" +
      "❓ /help — Show all commands\n\n" +
      "Or just *send a photo/PDF* of any document to analyze it for risky clauses.",
      { parse_mode: "Markdown" }
    )
  );

  bot.command("help", (ctx) =>
    ctx.reply(
      "*ArthSathi Commands:*\n\n" +
      "📋 /schemes — Find government schemes you qualify for\n" +
      "🗺️ /roadmap — Get a personalised financial plan\n" +
      "📄 /summary — Get summary of your last document analysis\n" +
      "📸 Send photo/PDF — Analyze document for risky clauses\n" +
      "🎙️ Send voice note — Ask anything by voice\n\n" +
      "*Type a number to quick-access:*\n" +
      "1 → Schemes  2 → Roadmap  3 → Document help",
      { parse_mode: "Markdown" }
    )
  );

  bot.command("schemes", async (ctx) => {
    const msg = await ctx.reply("🔍 Finding eligible schemes for you...");
    const result = await sendToBackend({
      user_id: String(ctx.from.id),
      channel: "telegram",
      intent: "scheme_match",
      detected_language: "hi",
    });
    await ctx.api.editMessageText(ctx.chat.id, msg.message_id,
      result.text_response || "No schemes found. Complete your profile first.",
      { parse_mode: "Markdown" }
    ).catch(() => ctx.reply(result.text_response || "No schemes found."));
  });

  bot.command("roadmap", async (ctx) => {
    const msg = await ctx.reply("📊 Building your financial roadmap...");
    const result = await sendToBackend({
      user_id: String(ctx.from.id),
      channel: "telegram",
      intent: "financial_roadmap",
      detected_language: "hi",
    });
    await ctx.api.editMessageText(ctx.chat.id, msg.message_id,
      result.text_response || "Could not generate roadmap.",
      { parse_mode: "Markdown" }
    ).catch(() => ctx.reply(result.text_response || "Could not generate roadmap."));
  });

  bot.command("summary", async (ctx) => {
    try {
      const resp = await axios.get(`${BACKEND_URL}/documents/summary/latest`, { timeout: 10000 });
      const data = resp.data;

      if (data.message) {
        return ctx.reply("📭 " + data.message);
      }

      const flags = data.risk_flags || [];
      const high   = flags.filter(f => f.risk_level === "high").length;
      const medium = flags.filter(f => f.risk_level === "medium").length;

      let reply = `📋 *Last Document Summary*\n\n${data.summary}\n\n`;
      reply += `🔴 High: ${high}  🟡 Medium: ${medium}  📅 ${new Date(data.analyzed_at).toLocaleDateString()}`;

      if (flags.length > 0) {
        reply += "\n\n*Top Risk Clauses:*\n";
        flags.slice(0, 3).forEach(f => {
          const emoji = f.risk_level === "high" ? "🔴" : f.risk_level === "medium" ? "🟡" : "🔵";
          reply += `${emoji} ${f.explanation}\n`;
        });
      }

      await ctx.reply(reply, { parse_mode: "Markdown" });
    } catch {
      ctx.reply("Could not fetch summary. Send a document first to analyze it.");
    }
  });

  // ── Voice notes ────────────────────────────────────────────────────────────

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
    await ctx.reply(result.text_response || "Sorry, could not process audio. Please type your question.");
  });

  // ── Photos and documents ───────────────────────────────────────────────────

  bot.on(["message:photo", "message:document"], async (ctx) => {
    const msg = await ctx.reply("📄 Analyzing your document for risky clauses...");

    try {
      let fileId, fileName, contentType;

      if (ctx.message.photo) {
        fileId      = ctx.message.photo[ctx.message.photo.length - 1].file_id;
        fileName    = "document.jpg";
        contentType = "image/jpeg";
      } else {
        fileId      = ctx.message.document.file_id;
        fileName    = ctx.message.document.file_name || "document";
        contentType = ctx.message.document.mime_type || "image/jpeg";
      }

      const fileResp = await axios.get(`https://api.telegram.org/bot${token}/getFile?file_id=${fileId}`);
      const filePath = fileResp.data.result.file_path;
      const fileUrl  = `https://api.telegram.org/file/bot${token}/${filePath}`;

      const fileData = await axios.get(fileUrl, { responseType: "arraybuffer" });
      const fileBuffer = Buffer.from(fileData.data);

      const form = new FormData();
      form.append("file", fileBuffer, { filename: fileName, contentType });

      const resp = await axios.post(
        `${BACKEND_URL}/documents/analyze?lang=en`,
        form,
        { headers: form.getHeaders(), timeout: 60000 }
      );

      const data  = resp.data;
      const flags = data.risk_flags || [];
      const high   = flags.filter(f => f.risk_level === "high").length;
      const medium = flags.filter(f => f.risk_level === "medium").length;
      const low    = flags.filter(f => f.risk_level === "low").length;

      let reply = `📋 *Document Analysis*\n\n`;
      reply += `${data.summary}\n\n`;

      if (flags.length > 0) {
        reply += `*Risk Summary:* 🔴 ${high} High  🟡 ${medium} Medium  🔵 ${low} Low\n\n`;
        reply += `*Clauses Found:*\n`;
        flags.slice(0, 6).forEach(f => {
          const emoji = f.risk_level === "high" ? "🔴" : f.risk_level === "medium" ? "🟡" : "🔵";
          reply += `${emoji} ${f.explanation}\n`;
        });
        if (flags.length > 6) reply += `\n_...and ${flags.length - 6} more. Use /summary to see all._`;
      } else {
        reply += "✅ No risky clauses detected.";
      }

      reply += "\n\n_Use /summary to see this analysis again._";

      await ctx.api.editMessageText(ctx.chat.id, msg.message_id, reply, { parse_mode: "Markdown" })
        .catch(() => ctx.reply(reply, { parse_mode: "Markdown" }));

    } catch (err) {
      console.error("[Telegram] Document error:", err.response?.data || err.message);
      await ctx.api.editMessageText(ctx.chat.id, msg.message_id,
        "❌ Could not analyze document. Please try a clearer image or a typed PDF."
      ).catch(() => {});
    }
  });

  // ── Plain text ─────────────────────────────────────────────────────────────

  bot.on("message:text", async (ctx) => {
    const text = ctx.message.text.trim();

    // Number shortcuts
    const shortcuts = {
      "1": "scheme_match",
      "2": "financial_roadmap",
      "3": "document_analysis",
    };

    if (shortcuts[text]) {
      if (text === "3") return ctx.reply("📸 Please send a photo or PDF of your document to analyze it.");
      const result = await sendToBackend({
        user_id: String(ctx.from.id),
        channel: "telegram",
        intent: shortcuts[text],
        detected_language: "hi",
      });
      return ctx.reply(result.text_response || "Could not get response.", { parse_mode: "Markdown" });
    }

    const result = await sendToBackend({
      user_id: String(ctx.from.id),
      channel: "telegram",
      raw_text: text,
      detected_language: "hi",
    });
    await ctx.reply(result.text_response || "Sorry, I didn't understand that. Type /help for options.");
  });

  bot.catch((err) => console.error("[Telegram] Error:", err.message));
  bot.start();
  console.log("[Telegram] Bot started");
}
