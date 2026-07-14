import {
  createUIMessageStream,
  createUIMessageStreamResponse,
} from "ai";

export async function POST(request) {
  try {
    const body = await request.json();
    const messages = body.messages ?? [];

    const stream = createUIMessageStream({
      execute({ writer }) {
        const textId = crypto.randomUUID();

        writer.write({
          type: "text-start",
          id: textId,
        });

        writer.write({
          type: "text-delta",
          id: textId,
          delta: "This is a generic response from the chat endpoint. This is a generic response from the chat endpoint. This is a generic response from the chat endpoint. This is a generic response from the chat endpoint.This is a generic response from the chat endpoint.This is a generic response from the chat endpoint.This is a generic response from the chat endpoint.",
        });

        writer.write({
          type: "text-end",
          id: textId,
        });
      },

      onError(error) {
        console.error("Chat stream error:", error);
        return "Something went wrong while generating the response.";
      },
    });

    return createUIMessageStreamResponse({
      status: 200,
      stream,
    });
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