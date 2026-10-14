// FlowCraft - Agentic Task Decomposer Client Logic
let currentPlan = null;
let currentFocusIndex = 0;
let timerSeconds = 15 * 60;
let timerInterval = null;
let isTimerRunning = false;
let stuckStepContext = null;

// DOM Elements
const formSection = document.getElementById("formSection");
const planSection = document.getElementById("planSection");
const decomposeForm = document.getElementById("decomposeForm");
const taskInput = document.getElementById("taskInput");
const techStackInput = document.getElementById("techStackInput");
const timeBudgetSelect = document.getElementById("timeBudgetSelect");
const expLevelSelect = document.getElementById("expLevelSelect");
const btnSubmit = document.getElementById("btnSubmit");

// Plan UI
const planTitle = document.getElementById("planTitle");
const planSummary = document.getElementById("planSummary");
const planStackPill = document.getElementById("planStackPill");
const planTimePill = document.getElementById("planTimePill");
const planStepCountPill = document.getElementById("planStepCountPill");
const progressBar = document.getElementById("progressBar");
const progressText = document.getElementById("progressText");
const progressPercent = document.getElementById("progressPercent");
const stepsList = document.getElementById("stepsList");
const btnLaunchFocus = document.getElementById("btnLaunchFocus");
const btnExportMarkdown = document.getElementById("btnExportMarkdown");
const btnNewPlan = document.getElementById("btnNewPlan");

// Focus Mode UI
const focusModal = document.getElementById("focusModal");
const btnCloseFocus = document.getElementById("btnCloseFocus");
const focusPhaseName = document.getElementById("focusPhaseName");
const focusStepNum = document.getElementById("focusStepNum");
const focusStepTitle = document.getElementById("focusStepTitle");
const focusStepDesc = document.getElementById("focusStepDesc");
const focusCommandsBox = document.getElementById("focusCommandsBox");
const focusCommandsCode = document.getElementById("focusCommandsCode");
const focusStarterCodeBox = document.getElementById("focusStarterCodeBox");
const focusStarterCode = document.getElementById("focusStarterCode");
const focusFilePathLabel = document.getElementById("focusFilePathLabel");
const focusDefinitionOfDone = document.getElementById("focusDefinitionOfDone");
const focusPitfallsBox = document.getElementById("focusPitfallsBox");
const focusPitfallsText = document.getElementById("focusPitfallsText");
const timerDisplay = document.getElementById("timerDisplay");
const btnTimerToggle = document.getElementById("btnTimerToggle");
const btnTimerReset = document.getElementById("btnTimerReset");
const btnFocusPrev = document.getElementById("btnFocusPrev");
const btnFocusComplete = document.getElementById("btnFocusComplete");
const btnFocusUnblock = document.getElementById("btnFocusUnblock");

// Modals
const settingsModal = document.getElementById("settingsModal");
const btnSettings = document.getElementById("btnSettings");
const btnCloseSettings = document.getElementById("btnCloseSettings");
const apiKeyInput = document.getElementById("apiKeyInput");
const btnSaveApiKey = document.getElementById("btnSaveApiKey");
const apiKeyStatusLabel = document.getElementById("apiKeyStatusLabel");

const unblockModal = document.getElementById("unblockModal");
const btnCloseUnblock = document.getElementById("btnCloseUnblock");
const unblockStepContext = document.getElementById("unblockStepContext");
const unblockInput = document.getElementById("unblockInput");
const btnSubmitUnblock = document.getElementById("btnSubmitUnblock");
const unblockResultBox = document.getElementById("unblockResultBox");
const unblockDiagnosis = document.getElementById("unblockDiagnosis");
const unblockQuickFix = document.getElementById("unblockQuickFix");
const unblockSubstepsList = document.getElementById("unblockSubstepsList");
const unblockCmdBox = document.getElementById("unblockCmdBox");
const unblockCmdText = document.getElementById("unblockCmdText");

const historyModal = document.getElementById("historyModal");
const btnPastPlans = document.getElementById("btnPastPlans");
const btnCloseHistory = document.getElementById("btnCloseHistory");
const historyList = document.getElementById("historyList");

// --- Initialization ---
document.addEventListener("DOMContentLoaded", () => {
  updateApiKeyBadge();
  setupPresetPills();
  setupEventListeners();
  loadLastPlanIfAvailable();
});

function getSavedApiKey() {
  return localStorage.getItem("flowcraft_gemini_key") || "";
}

function updateApiKeyBadge() {
  const key = getSavedApiKey();
  if (key) {
    apiKeyStatusLabel.textContent = "✨ AI Active";
    apiKeyStatusLabel.style.color = "#a5b4fc";
  } else {
    apiKeyStatusLabel.textContent = "🔑 API Key";
    apiKeyStatusLabel.style.color = "";
  }
}

function setupPresetPills() {
  document.querySelectorAll(".preset-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      taskInput.value = pill.getAttribute("data-task");
      techStackInput.value = pill.getAttribute("data-stack");
      taskInput.focus();
    });
  });
}

function setupEventListeners() {
  // Decompose Form Submit
  decomposeForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const task = taskInput.value.trim();
    if (!task) return;

    setLoading(true);
    try {
      const payload = {
        task,
        tech_stack: techStackInput.value.trim() || "Python",
        available_time_minutes: parseInt(timeBudgetSelect.value, 10),
        experience_level: expLevelSelect.value,
        api_key: getSavedApiKey() || null
      };

      const res = await fetch("/api/decompose", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Decomposition failed");
      }

      currentPlan = await res.json();
      localStorage.setItem("flowcraft_last_plan_id", currentPlan.id);
      renderPlan(currentPlan);
    } catch (err) {
      alert("Error decomposing task: " + err.message);
    } finally {
      setLoading(false);
    }
  });

  // Settings Modal
  btnSettings.addEventListener("click", () => {
    apiKeyInput.value = getSavedApiKey();
    settingsModal.style.display = "flex";
  });
  btnCloseSettings.addEventListener("click", () => settingsModal.style.display = "none");
  btnSaveApiKey.addEventListener("click", () => {
    const val = apiKeyInput.value.trim();
    if (val) {
      localStorage.setItem("flowcraft_gemini_key", val);
    } else {
      localStorage.removeItem("flowcraft_gemini_key");
    }
    updateApiKeyBadge();
    settingsModal.style.display = "none";
  });

  // Past Plans Modal
  btnPastPlans.addEventListener("click", async () => {
    historyModal.style.display = "flex";
    historyList.innerHTML = "<p class='text-muted'>Loading plans...</p>";
    try {
      const res = await fetch("/api/plans");
      const plans = await res.json();
      if (!plans || plans.length === 0) {
        historyList.innerHTML = "<p class='text-muted'>No saved plans found. Decompose your first task!</p>";
        return;
      }
      historyList.innerHTML = plans.map(p => `
        <div class="history-item" onclick="loadPlanById('${p.id}')">
          <div>
            <div class="history-title">${escapeHtml(p.title)}</div>
            <div class="history-meta">${escapeHtml(p.tech_stack)} • ~${p.total_estimated_minutes} min • ${new Date(p.created_at).toLocaleDateString()}</div>
          </div>
          <div class="history-badge">${p.completed_steps}/${p.total_steps} done (${p.progress_pct}%)</div>
        </div>
      `).join("");
    } catch (e) {
      historyList.innerHTML = "<p class='text-muted'>Failed to load history.</p>";
    }
  });
  btnCloseHistory.addEventListener("click", () => historyModal.style.display = "none");

  // New Plan button
  btnNewPlan.addEventListener("click", () => {
    planSection.style.display = "none";
    formSection.style.display = "block";
    taskInput.value = "";
    taskInput.focus();
  });

  // Launch Focus Mode
  btnLaunchFocus.addEventListener("click", () => {
    if (!currentPlan || !currentPlan.steps.length) return;
    // Find first uncompleted step or start at 0
    const pendingIdx = currentPlan.steps.findIndex(s => s.status !== "completed");
    openFocusMode(pendingIdx !== -1 ? pendingIdx : 0);
  });

  // Close Focus Mode
  btnCloseFocus.addEventListener("click", closeFocusMode);

  // Timer Controls
  btnTimerToggle.addEventListener("click", toggleTimer);
  btnTimerReset.addEventListener("click", resetTimer);

  // Focus navigation & completion
  btnFocusPrev.addEventListener("click", () => {
    if (currentFocusIndex > 0) {
      openFocusMode(currentFocusIndex - 1);
    }
  });

  btnFocusComplete.addEventListener("click", async () => {
    if (!currentPlan) return;
    const step = currentPlan.steps[currentFocusIndex];
    await toggleStepStatus(step.id, "completed");
    
    // Check if more steps exist
    if (currentFocusIndex < currentPlan.steps.length - 1) {
      openFocusMode(currentFocusIndex + 1);
    } else {
      triggerConfetti();
      closeFocusMode();
      alert("🎉 Incredible job! You completed all steps in this Flow Plan!");
    }
  });

  // Export Markdown
  btnExportMarkdown.addEventListener("click", () => {
    if (!currentPlan) return;
    window.open(`/api/export/${currentPlan.id}`, "_blank");
  });

  // Unblock Modal Submit
  btnSubmitUnblock.addEventListener("click", async () => {
    if (!stuckStepContext) return;
    const problem = unblockInput.value.trim();
    if (!problem) {
      alert("Please describe what error or problem you're seeing.");
      return;
    }

    document.getElementById("unblockBtnText").style.display = "none";
    document.getElementById("unblockBtnLoader").style.display = "inline";

    try {
      const payload = {
        step_id: stuckStepContext.id,
        step_title: stuckStepContext.title,
        step_description: stuckStepContext.description,
        problem_details: problem,
        api_key: getSavedApiKey() || null
      };

      const res = await fetch("/api/unblock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      unblockDiagnosis.textContent = data.diagnosis;
      unblockQuickFix.textContent = data.quick_fix;
      unblockSubstepsList.innerHTML = (data.micro_substeps || []).map(s => `<li>${escapeHtml(s)}</li>`).join("");

      if (data.suggested_commands && data.suggested_commands.length > 0) {
        unblockCmdBox.style.display = "block";
        unblockCmdText.textContent = data.suggested_commands.join("\n");
      } else {
        unblockCmdBox.style.display = "none";
      }

      unblockResultBox.style.display = "block";
    } catch (err) {
      alert("Unblock request failed: " + err.message);
    } finally {
      document.getElementById("unblockBtnText").style.display = "inline";
      document.getElementById("unblockBtnLoader").style.display = "none";
    }
  });

  btnCloseUnblock.addEventListener("click", () => unblockModal.style.display = "none");

  btnFocusUnblock.addEventListener("click", () => {
    if (!currentPlan) return;
    const step = currentPlan.steps[currentFocusIndex];
    triggerUnblockModal(step);
  });
}

function setLoading(isLoading) {
  const btnText = btnSubmit.querySelector(".btn-text");
  const btnLoader = btnSubmit.querySelector(".btn-loader");
  if (isLoading) {
    btnSubmit.disabled = true;
    btnText.style.display = "none";
    btnLoader.style.display = "inline-flex";
  } else {
    btnSubmit.disabled = false;
    btnText.style.display = "inline";
    btnLoader.style.display = "none";
  }
}

async function loadLastPlanIfAvailable() {
  const lastId = localStorage.getItem("flowcraft_last_plan_id");
  if (lastId) {
    try {
      const res = await fetch(`/api/plans/${lastId}`);
      if (res.ok) {
        currentPlan = await res.json();
        renderPlan(currentPlan);
      }
    } catch (e) {
      console.warn("Could not load previous plan", e);
    }
  }
}

window.loadPlanById = async function(planId) {
  try {
    const res = await fetch(`/api/plans/${planId}`);
    if (res.ok) {
      currentPlan = await res.json();
      localStorage.setItem("flowcraft_last_plan_id", currentPlan.id);
      renderPlan(currentPlan);
      historyModal.style.display = "none";
    }
  } catch (e) {
    alert("Failed to load plan: " + e.message);
  }
};

function renderPlan(plan) {
  formSection.style.display = "none";
  planSection.style.display = "block";

  planTitle.textContent = plan.title;
  planSummary.textContent = plan.summary;
  planStackPill.textContent = plan.tech_stack;
  planTimePill.textContent = `~${plan.total_estimated_minutes} min`;
  planStepCountPill.textContent = `${plan.steps.length} Steps`;

  renderSteps(plan);
  updateProgressBar(plan);
}

function renderSteps(plan) {
  let html = "";
  let currentPhase = null;

  plan.steps.forEach((step, idx) => {
    if (step.phase !== currentPhase) {
      currentPhase = step.phase;
      html += `
        <div class="phase-separator">
          <span class="phase-tag">${escapeHtml(currentPhase)}</span>
        </div>
      `;
    }

    const isDone = step.status === "completed";
    html += `
      <div class="step-card ${isDone ? 'completed' : ''}" id="card-${step.id}">
        <div class="step-card-header">
          <div class="step-title-col">
            <div class="step-status-icon" onclick="toggleStepStatus('${step.id}', '${isDone ? 'pending' : 'completed'}')">
              ${isDone ? '✓' : ''}
            </div>
            <div>
              <h3 class="step-title">${escapeHtml(step.title)}</h3>
            </div>
          </div>
          <span class="step-time-badge">~${step.estimated_minutes}m</span>
        </div>

        <p class="step-desc">${escapeHtml(step.description)}</p>

        ${step.commands && step.commands.length > 0 ? `
          <div class="code-box-container">
            <div class="code-box-header">
              <span>Terminal Command</span>
              <button class="btn-copy" onclick="copyText('${escapeHtml(step.commands.join(' && '))}', this)">Copy</button>
            </div>
            <pre><code class="language-bash">${escapeHtml(step.commands.join('\n'))}</code></pre>
          </div>
        ` : ''}

        ${step.starter_code ? `
          <div class="code-box-container">
            <div class="code-box-header">
              <span>${escapeHtml(step.file_path || 'Starter Code')}</span>
              <button class="btn-copy" onclick="copyText(${JSON.stringify(step.starter_code)}, this)">Copy Code</button>
            </div>
            <pre><code>${escapeHtml(step.starter_code)}</code></pre>
          </div>
        ` : ''}

        <div class="definition-of-done-card">
          <strong>✅ Definition of Done:</strong> ${escapeHtml(step.definition_of_done)}
        </div>

        ${step.pitfalls && step.pitfalls.length > 0 ? `
          <div class="pitfall-box">
            <strong>⚠️ Watch out:</strong> ${escapeHtml(step.pitfalls[0])}
          </div>
        ` : ''}

        <div class="step-card-footer">
          <button class="btn btn-secondary btn-small" onclick="openFocusMode(${idx})">
            🎯 Focus On This Step
          </button>
          <button class="btn btn-danger btn-small" onclick="triggerUnblockModalByIndex(${idx})">
            🚨 I'm Stuck
          </button>
        </div>
      </div>
    `;
  });

  stepsList.innerHTML = html;
}

function updateProgressBar(plan) {
  const completed = plan.steps.filter(s => s.status === "completed").length;
  const total = plan.steps.length;
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

  progressBar.style.width = `${pct}%`;
  progressText.textContent = `${completed} of ${total} Steps Complete`;
  progressPercent.textContent = `${pct}%`;
}

window.toggleStepStatus = async function(stepId, newStatus) {
  if (!currentPlan) return;
  try {
    const res = await fetch(`/api/plans/${currentPlan.id}/steps/${stepId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    if (res.ok) {
      currentPlan = await res.json();
      renderPlan(currentPlan);
      if (newStatus === "completed") {
        triggerConfettiMini();
      }
    }
  } catch (e) {
    console.error("Failed to update status", e);
  }
};

// Focus Mode Logic
function openFocusMode(stepIndex) {
  if (!currentPlan || !currentPlan.steps[stepIndex]) return;
  currentFocusIndex = stepIndex;
  const step = currentPlan.steps[stepIndex];

  focusPhaseName.textContent = step.phase;
  focusStepNum.textContent = `Step ${stepIndex + 1} of ${currentPlan.steps.length}`;
  focusStepTitle.textContent = step.title;
  focusStepDesc.textContent = step.description;
  focusDefinitionOfDone.textContent = step.definition_of_done;

  if (step.commands && step.commands.length > 0) {
    focusCommandsBox.style.display = "block";
    focusCommandsCode.textContent = step.commands.join("\n");
  } else {
    focusCommandsBox.style.display = "none";
  }

  if (step.starter_code) {
    focusStarterCodeBox.style.display = "block";
    focusStarterCode.textContent = step.starter_code;
    focusFilePathLabel.textContent = step.file_path || "Starter Code";
  } else {
    focusStarterCodeBox.style.display = "none";
  }

  if (step.pitfalls && step.pitfalls.length > 0) {
    focusPitfallsBox.style.display = "block";
    focusPitfallsText.textContent = step.pitfalls[0];
  } else {
    focusPitfallsBox.style.display = "none";
  }

  btnFocusPrev.disabled = (stepIndex === 0);
  btnFocusComplete.textContent = (stepIndex === currentPlan.steps.length - 1) 
    ? "✅ Finish Final Step 🎉" 
    : "✅ Mark Done & Next →";

  // Reset timer to step duration
  timerSeconds = (step.estimated_minutes || 15) * 60;
  pauseTimer();
  updateTimerDisplay();

  focusModal.style.display = "flex";
  document.body.style.overflow = "hidden";
}

function closeFocusMode() {
  pauseTimer();
  focusModal.style.display = "none";
  document.body.style.overflow = "";
}

function updateTimerDisplay() {
  const m = Math.floor(timerSeconds / 60);
  const s = timerSeconds % 60;
  timerDisplay.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function toggleTimer() {
  if (isTimerRunning) {
    pauseTimer();
  } else {
    startTimer();
  }
}

function startTimer() {
  isTimerRunning = true;
  btnTimerToggle.textContent = "Pause Timer";
  btnTimerToggle.classList.replace("btn-primary", "btn-secondary");

  timerInterval = setInterval(() => {
    if (timerSeconds > 0) {
      timerSeconds--;
      updateTimerDisplay();
    } else {
      pauseTimer();
      alert("⏰ Time is up for this micro-step! Feel free to wrap up or click 'Mark Done'!");
    }
  }, 1000);
}

function pauseTimer() {
  isTimerRunning = false;
  btnTimerToggle.textContent = "Start Timer";
  btnTimerToggle.classList.replace("btn-secondary", "btn-primary");
  if (timerInterval) clearInterval(timerInterval);
}

function resetTimer() {
  pauseTimer();
  const step = currentPlan?.steps[currentFocusIndex];
  timerSeconds = (step?.estimated_minutes || 15) * 60;
  updateTimerDisplay();
}

// Unblocker Modal
window.triggerUnblockModalByIndex = function(idx) {
  if (!currentPlan) return;
  triggerUnblockModal(currentPlan.steps[idx]);
};

function triggerUnblockModal(step) {
  stuckStepContext = step;
  unblockStepContext.textContent = `Step: ${step.title}`;
  unblockInput.value = "";
  unblockResultBox.style.display = "none";
  unblockModal.style.display = "flex";
}

// Copy utilities
window.copyText = function(text, btnElement) {
  navigator.clipboard.writeText(text);
  if (btnElement) {
    const orig = btnElement.textContent;
    btnElement.textContent = "Copied!";
    setTimeout(() => { btnElement.textContent = orig; }, 1500);
  }
};

window.copyFocusCommands = function() {
  const code = focusCommandsCode.textContent;
  navigator.clipboard.writeText(code);
  alert("Terminal commands copied to clipboard!");
};

window.copyFocusStarterCode = function() {
  const code = focusStarterCode.textContent;
  navigator.clipboard.writeText(code);
  alert("Starter code copied to clipboard!");
};

function triggerConfetti() {
  if (window.confetti) {
    window.confetti({ particleCount: 120, spread: 80, origin: { y: 0.6 } });
  }
}

function triggerConfettiMini() {
  if (window.confetti) {
    window.confetti({ particleCount: 30, spread: 50, origin: { y: 0.8 } });
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
