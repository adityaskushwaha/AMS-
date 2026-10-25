import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

export const askAI = createServerFn({ method: "POST" })
  .inputValidator((d: unknown) =>
    z.object({ question: z.string().min(1).max(1000), context: z.string().max(20000) }).parse(d),
  )
  .handler(async ({ data }) => {
    const { createOpenAI } = await import("@ai-sdk/openai");
    const { streamText } = await import("ai");
    const key = process.env["LOVABLE_API_KEY"];
    if (!key) return { error: "AI is not configured.", text: "" };
    const openai = createOpenAI({
      baseURL: "https://ai.gateway.lovable.dev/v1",
      apiKey: key,
      headers: { "Lovable-API-Key": key, "X-Lovable-AIG-SDK": "vercel-ai-sdk" },
    });
    try {
      const result = streamText({
        model: openai.responses("openai/gpt-6-astra") as unknown as Parameters<typeof streamText>[0]["model"],
        system:
          "You are the assistant of AMS, an AI-driven attendance monitoring system for a college. Answer concisely using the attendance data given. Use short bullet points. Flag students below 75% as at-risk. Suggest practical actions.",
        prompt: `Attendance data:\n${data.context}\n\nQuestion: ${data.question}`,
        providerOptions: {
          openai: {
            forceReasoning: true,
            reasoningEffort: "low",
            reasoningSummary: "auto",
            store: false,
            include: ["reasoning.encrypted_content"],
          },
        },
      });
      const text = await result.text;
      return { error: null, text };
    } catch (e: unknown) {
      const status = (e as { statusCode?: number })?.statusCode;
      const msg =
        status === 429 ? "Too many requests — please try again shortly."
        : status === 402 ? "AI credits are used up for this workspace."
        : "The AI assistant could not answer right now.";
      return { error: msg, text: "" };
    }
  });
