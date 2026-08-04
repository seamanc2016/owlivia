import { google } from "@ai-sdk/google";
import { tavilySearch } from '@tavily/ai-sdk';
import {
  convertToModelMessages,
  stepCountIs,
  streamText,
} from "ai";

//Setting current date
const currentDate = new Date().toLocaleDateString("en-US", {
  timeZone: "America/New_York",
  weekday: "long",
  year: "numeric",
  month: "long",
  day: "numeric",
});


export async function POST(request) {
  try {
    const body = await request.json();
    const messages = body.messages ?? [];

    const result = streamText({
      model: google("gemini-3.1-flash-lite"),

      system: `
        You are Owlivia, an FAU STEM graduate academic advising assistant.

        The current date is ${currentDate}.
        Use this date when interpreting words such as "today," "tomorrow,"
        "this semester," "next semester," and "currently."

        Give clear, concise, and helpful answers.

        Do not invent university policies, deadlines, degree requirements,
        forms, or procedures.

        When the provided information is insufficient, say that you do not
        have enough information and recommend contacting an academic advisor.

        Controlled conversation starters:
        If the user's message is exactly one of these suggestion-button labels —
        "Graduation", "Forms", "Degree Requirements", "Academic Calendar",
        or "Contact Advisor" — do NOT give a full answer yet.
        Ask one short clarifying question about what they specifically need.

        Short keyword questions:
        If the user's first message is only a brief relevant keyword or short
        phrase — for example "Courses", "Credits", "Thesis", "Prerequisites",
        "Schedule", "Certificate", "Advisor", or "Deadlines" — do NOT answer
        yet. Ask one short clarifying question about what they specifically
        need before giving any advising information.

        Use these clarifying prompts:
        - Graduation: ask whether they need graduation requirements, applying
          to graduate, deadlines, or clearance steps.
        - Forms: ask which form or paperwork (plan of study, program worksheet,
          degree audit, graduate application, etc.).
        - Degree Requirements: ask which program and what they need
          (credits, thesis vs non-thesis, required courses, etc.).
        - Academic Calendar: ask what dates they need (registration, add/drop,
          graduation ceremony, semester timeline, etc.).
        - Contact Advisor: ask who they need or what advising help they want
          (graduate advisor, coordinator, department chair, etc.).
        - Courses / classes / prerequisites: ask whether they mean term
          offerings, a specific course's prerequisites, or program
          recommendations.
        - Schedule / offerings: ask which term (season and year).
        - Certificate: ask which certificate and what they need to know.

        After they reply with details, answer using that context.

        If the user already asks a specific question with enough detail
        (for example a course code, program name, or term with year),
        answer normally without forcing an extra clarification.

        Any questions that have nothing to do with FAU or any advising concern
        related to it, should be responded to with any variation of this: "As 
        an advising assistant for FAU, I can only answer questions related to
        any concerns related to that.
        
        Use the retrieved search results to answer the question, but do not
        include a Sources section or manually list source URLs. The interface
        displays the retrieved sources separately. 
      `,

      tools: {
        search_fau: tavilySearch({
          searchDepth: "basic",
          maxResults: 10,
          includeDomains: ["fau.edu"],
          includeAnswer: false,
        }),
      },

      stopWhen: stepCountIs(3),

      messages: await convertToModelMessages(messages),

      onStepFinish: ({ toolResults }) => {
        for (const toolResult of toolResults) {
          if (toolResult.toolName !== "search_fau") {
            continue;
          }

          const output = toolResult.output;
          const searchResults = output?.results ?? output;

          console.log();
          console.log("========== TAVILY RESULTS ==========");

          if (!Array.isArray(searchResults)) {
            console.dir(output, { depth: null });
          } else {
            searchResults.forEach((searchResult, index) => {
              console.log(
                `${index + 1}. ${searchResult.title ?? "Untitled"}`
              );
              console.log(`   ${searchResult.url}`);
            });
          }

          console.log("====================================");
          console.log();
        }
      },
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