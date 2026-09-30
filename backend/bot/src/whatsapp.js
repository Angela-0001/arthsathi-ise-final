import twilio from "twilio";
import { sendToBackend } from "./gateway.js";

const twiml = twilio.twiml;

export async function whatsappWebhook(req, res) {
  const { From, Body, MediaUrl0, MediaContentType0 } = req.body;

  const msg = {
    user_id: From,
    channel: "whatsapp",
    raw_text: Body || null,
    detected_language: "hi",
    payload: null,
  };

  if (MediaUrl0 && MediaContentType0?.startsWith("image/")) {
    msg.intent = "document_analysis";
    msg.payload = { media_url: MediaUrl0 };
  }

  const result = await sendToBackend(msg);

  const response = new twiml.MessagingResponse();
  response.message(result.text_response || "Sorry, something went wrong.");
  res.type("text/xml").send(response.toString());
}
