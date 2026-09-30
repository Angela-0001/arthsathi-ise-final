import "dotenv/config";
import express from "express";
import { startTelegramBot } from "./telegram.js";
import { whatsappWebhook } from "./whatsapp.js";

const app = express();
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

app.post("/whatsapp/webhook", whatsappWebhook);
app.get("/health", (_, res) => res.json({ status: "ok", service: "arthsathi-bot" }));

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`[Bot] Running on port ${PORT}`));

startTelegramBot();
