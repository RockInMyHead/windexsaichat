async function sendPrompt() {
  const prompt = document.getElementById("prompt").value;
  const result = document.getElementById("result");
  const iframe = document.getElementById("preview");

  const messages = [
    {
      role: "system",
      content: "Ты эксперт по созданию сайтов. Возвращай только HTML внутри маркеров: NEW_PAGE_START/NEW_PAGE_END и TITLE_PAGE_START/END."
    },
    {
      role: "user",
      content: prompt
    }
  ];

  const resp = await fetch("/api/ai-editor", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, model: "gpt-4" })
  });

  const reader = resp.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let fullText = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value);
    fullText += chunk;
    result.textContent = fullText;
  }

  const match = fullText.match(/NEW_PAGE_START([\s\S]*?)NEW_PAGE_END/);
  if (match) {
    const html = match[1];
    iframe.srcdoc = html;
  }
}

document.getElementById('generate-btn').addEventListener('click', sendPrompt);
