import { google } from "@ai-sdk/google";
import { convertToModelMessages, streamText } from "ai";

export async function POST(request) {
  try {
    const body = await request.json();
    const messages = body.messages ?? [];

    const result = streamText({
      model: google("gemini-3.1-flash-lite"),

      system: `
        You are Owlivia, an FAU STEM graduate academic advising assistant.

        Give clear, concise, and helpful answers.

        Do not invent university policies, deadlines, degree requirements,
        forms, or procedures.

        When the provided information is insufficient, say that you do not
        have enough information and recommend contacting an academic advisor.
      `,

      messages: await convertToModelMessages(messages),
    });

    return result.toUIMessageStreamResponse();
  } catch (error) {
    console.error("Chat route error:", error);

    return Response.json(
      {
        error: "Unable to process the chat request.",
      },
      {
        status: 500,
      }
    );
  }
}