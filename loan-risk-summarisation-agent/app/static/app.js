const form = document.getElementById("uploadForm");
const message = document.getElementById("message");
const result = document.getElementById("result");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const fileInput = document.getElementById("file");
  if (!fileInput.files.length) return;

  const data = new FormData();
  data.append("file", fileInput.files[0]);

  message.textContent = "Evaluating document...";
  result.classList.add("hidden");

  try {
    const response = await fetch("/api/evaluate", {
      method: "POST",
      body: data
    });

    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.detail || "Evaluation failed.");
    }

    document.getElementById("filename").textContent = payload.filename;
    document.getElementById("riskScore").textContent = `${payload.risk_score}/100`;
    document.getElementById("riskBadge").textContent = payload.risk_level + " Risk";
    document.getElementById("applicant").textContent =
      payload.extracted_fields.applicant_name || "Not available";
    document.getElementById("loanAmount").textContent =
      money(payload.extracted_fields.loan_amount);
    document.getElementById("income").textContent =
      money(payload.extracted_fields.monthly_income);
    document.getElementById("summary").textContent = payload.summary;

    const flags = document.getElementById("flags");
    flags.innerHTML = "";
    if (!payload.risk_flags.length) {
      const li = document.createElement("li");
      li.textContent = "No major automated risk flags detected.";
      li.style.color = "#18794e";
      flags.appendChild(li);
    } else {
      payload.risk_flags.forEach(flag => {
        const li = document.createElement("li");
        li.textContent = flag;
        flags.appendChild(li);
      });
    }

    const fields = document.getElementById("fields");
    fields.innerHTML = "";
    Object.entries(payload.extracted_fields).forEach(([key, value]) => {
      const div = document.createElement("div");
      div.className = "field";
      div.innerHTML = `<small>${key.replaceAll("_", " ")}</small><strong>${value ?? "Not available"}</strong>`;
      fields.appendChild(div);
    });

    result.classList.remove("hidden");
    message.textContent = "Evaluation completed successfully.";
  } catch (error) {
    message.textContent = error.message;
  }
});

function money(value) {
  if (value === null || value === undefined) return "Not available";
  return "₹" + Number(value).toLocaleString("en-IN");
}
