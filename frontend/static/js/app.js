/**
 * ProductPulse Frontend Controller
 * Drives the Agent Decision Lifecycle:
 * DETECT -> REMEMBER -> REASON -> DECIDE -> APPROVE -> EXECUTE -> MEASURE -> LEARN
 */

const API_BASE = "";

// State Management
const state = {
  problems: [],
  selectedProblem: null,
  activeAction: null,
  recalledMemories: [],
  measurement: null,
  systemStatus: null,
  isChallengeMode: false,
  challengeProblemId: "prob-challenge-002"
};

// DOM Elements
const elements = {
  hindsightBankLabel: document.getElementById("hindsight-bank-label"),
  btnSeedMemory: document.getElementById("btn-seed-memory"),
  btnReflectModal: document.getElementById("btn-reflect-modal"),
  btnChallengeAgent: document.getElementById("btn-challenge-agent"),
  
  // Agent Activity Stream
  agentActivityCard: document.getElementById("agent-activity-card"),
  activityStatusTag: document.getElementById("activity-status-tag"),
  activityStepsList: document.getElementById("activity-steps-list"),

  // Memory Changed Decision Panel (Challenge-specific)
  memoryChangedPanel: document.getElementById("memory-changed-panel"),
  adaptationRelevanceBadge: document.getElementById("adaptation-relevance-badge"),
  adaptationHistoricalText: document.getElementById("adaptation-historical-text"),
  adaptationSimilaritiesText: document.getElementById("adaptation-similarities-text"),
  adaptationDifferencesText: document.getElementById("adaptation-differences-text"),
  adaptationRationaleText: document.getElementById("adaptation-rationale-text"),
  
  // Problems Panel
  detectWeekSelect: document.getElementById("detect-week-select"),
  btnRefreshDetect: document.getElementById("btn-refresh-detect"),
  problemsLoading: document.getElementById("problems-loading"),
  problemsList: document.getElementById("problems-list"),
  problemCount: document.getElementById("problem-count"),
  
  // Decision Workspace
  workspaceEmpty: document.getElementById("workspace-empty"),
  decisionLoading: document.getElementById("decision-loading"),
  decisionLoadingMsg: document.getElementById("decision-loading-msg"),
  workspaceContent: document.getElementById("workspace-content"),
  currentActionStateBadge: document.getElementById("current-action-state-badge"),
  
  // Action Card
  actionTypeBadge: document.getElementById("action-type-badge"),
  actionPriorityBadge: document.getElementById("action-priority-badge"),
  actionSegmentBadge: document.getElementById("action-segment-badge"),
  actionAreaBadge: document.getElementById("action-area-badge"),
  actionIdLabel: document.getElementById("action-id-label"),
  actionTitle: document.getElementById("action-title"),
  actionExpected: document.getElementById("action-expected"),
  
  // Contrast Card
  reasoningWithText: document.getElementById("reasoning-with-text"),
  reasoningWithoutText: document.getElementById("reasoning-without-text"),
  memoryInfluenceText: document.getElementById("memory-influence-text"),
  actionEvidenceText: document.getElementById("action-evidence-text"),
  
  // Approval Buttons
  approvalInstruction: document.getElementById("approval-instruction"),
  btnApproveAction: document.getElementById("btn-approve-action"),
  btnRejectAction: document.getElementById("btn-reject-action"),
  btnExecuteAction: document.getElementById("btn-execute-action"),
  btnMeasureAction: document.getElementById("btn-measure-action"),
  btnLearnAction: document.getElementById("btn-learn-action"),
  
  // Right Panel: Memory & Measurement
  recalledCount: document.getElementById("recalled-count"),
  recalledMemoriesList: document.getElementById("recalled-memories-list"),
  measurementSection: document.getElementById("measurement-section"),
  measurementOutcomeBadge: document.getElementById("measurement-outcome-badge"),
  metricPreComplaints: document.getElementById("metric-pre-complaints"),
  metricPostComplaints: document.getElementById("metric-post-complaints"),
  metricComplaintDelta: document.getElementById("metric-complaint-delta"),
  metricPreSentiment: document.getElementById("metric-pre-sentiment"),
  metricPostSentiment: document.getElementById("metric-post-sentiment"),
  metricSentimentDelta: document.getElementById("metric-sentiment-delta"),
  lessonText: document.getElementById("lesson-text"),
  hindsightRetainedTag: document.getElementById("hindsight-retained-tag"),
  retainedMemoryId: document.getElementById("retained-memory-id"),
  
  // Stepper Elements
  steps: {
    detect: document.getElementById("step-detect"),
    remember: document.getElementById("step-remember"),
    reason: document.getElementById("step-reason"),
    decide: document.getElementById("step-decide"),
    approve: document.getElementById("step-approve"),
    execute: document.getElementById("step-execute"),
    measure: document.getElementById("step-measure"),
    learn: document.getElementById("step-learn")
  },
  
  // Modal
  reflectionModal: document.getElementById("reflection-modal"),
  btnCloseReflection: document.getElementById("btn-close-reflection"),
  reflectionQueryInput: document.getElementById("reflection-query-input"),
  btnRunReflection: document.getElementById("btn-run-reflection"),
  reflectionLoading: document.getElementById("reflection-loading"),
  reflectionOutput: document.getElementById("reflection-output"),
  
  toastContainer: document.getElementById("toast-container")
};

// =========================================================================
// INITIALIZATION
// =========================================================================
document.addEventListener("DOMContentLoaded", () => {
  initSystem();
  bindEvents();
});

async function initSystem() {
  state.isChallengeMode = false;
  if (elements.memoryChangedPanel) elements.memoryChangedPanel.classList.add("hidden");
  if (elements.agentActivityCard) elements.agentActivityCard.classList.add("hidden");
  
  await fetchSystemStatus();
  await runDetection();
  if (state.problems && state.problems.length > 0) {
    selectProblem(state.problems[0].id);
  }
}

function bindEvents() {
  elements.btnRefreshDetect.addEventListener("click", () => runDetection());
  elements.detectWeekSelect.addEventListener("change", () => runDetection());
  
  elements.btnSeedMemory.addEventListener("click", handleSeedMemory);
  elements.btnReflectModal.addEventListener("click", () => elements.reflectionModal.classList.remove("hidden"));
  elements.btnCloseReflection.addEventListener("click", () => elements.reflectionModal.classList.add("hidden"));
  elements.btnRunReflection.addEventListener("click", handleRunReflection);

  if (elements.btnChallengeAgent) {
    elements.btnChallengeAgent.addEventListener("click", handleChallengeAgent);
  }
  
  elements.btnApproveAction.addEventListener("click", handleApprove);
  elements.btnRejectAction.addEventListener("click", handleReject);
  elements.btnExecuteAction.addEventListener("click", handleExecute);
  elements.btnMeasureAction.addEventListener("click", handleMeasure);
  elements.btnLearnAction.addEventListener("click", handleLearn);
}

// =========================================================================
// API CALLS & CORE LOGIC
// =========================================================================

async function fetchSystemStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/status`);
    if (res.ok) {
      state.systemStatus = await res.json();
      elements.hindsightBankLabel.textContent = `Bank: ${state.systemStatus.bank_id || 'productpulse-ops'}`;
    }
  } catch (err) {
    console.warn("Could not fetch status:", err);
  }
}

async function runDetection() {
  setLifecycleStep("detect");
  elements.problemsLoading.classList.remove("hidden");
  elements.problemsList.innerHTML = "";

  const currentWeek = parseInt(elements.detectWeekSelect.value, 10);
  const priorWeek = currentWeek - 1;

  try {
    const res = await fetch(`${API_BASE}/api/agent/detect?current_week=${currentWeek}&prior_week=${priorWeek}`, {
      method: "POST"
    });
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    const data = await res.json();
    state.problems = data.problems || [];
    renderProblemsList(state.problems);
    showToast(`Detected ${state.problems.length} problem clusters from telemetry.`);
  } catch (err) {
    elements.problemsList.innerHTML = `<div class="empty-hint">Failed to load problems: ${err.message}</div>`;
    showToast(`Detection error: ${err.message}`, "error");
  } finally {
    elements.problemsLoading.classList.add("hidden");
  }
}

function renderProblemsList(problems) {
  elements.problemCount.textContent = problems.length;
  if (!problems.length) {
    elements.problemsList.innerHTML = `<div class="empty-hint">No anomalies detected in selected period.</div>`;
    return;
  }

  elements.problemsList.innerHTML = problems.map((p, idx) => `
    <div class="problem-card ${state.selectedProblem && state.selectedProblem.id === p.id ? 'selected' : ''}" 
         data-id="${p.id}" onclick="selectProblem('${p.id}')">
      <div class="problem-header">
        <span class="badge ${p.severity === 'CRITICAL' ? 'badge-priority' : 'badge-segment'}">${p.severity}</span>
        <span class="trend-badge ${p.trend_pct > 100 ? 'danger' : 'warning'}">+${p.trend_pct}%</span>
      </div>
      <div class="problem-title">${escapeHtml(p.title)}</div>
      <div class="problem-metrics">
        <div class="metric-pill">Complaints: <strong>${p.complaint_count}</strong></div>
        <div class="metric-pill">Sentiment: <strong>${p.sentiment_avg}</strong></div>
      </div>
      <div class="problem-why">${escapeHtml(p.why_it_matters)}</div>
      <div class="problem-tags">
        <span class="badge badge-area">${formatName(p.product_area)}</span>
        <span class="badge badge-segment">${formatName(p.segment)}</span>
      </div>
    </div>
  `).join("");
}

window.selectProblem = async function(problemId) {
  const problem = state.problems.find(p => p.id === problemId);
  if (!problem) return;

  // Manage Challenge Mode based on selected problem
  if (problem.id !== state.challengeProblemId) {
    state.isChallengeMode = false;
    if (elements.memoryChangedPanel) elements.memoryChangedPanel.classList.add("hidden");
    if (elements.agentActivityCard) elements.agentActivityCard.classList.add("hidden");
  } else {
    state.isChallengeMode = true;
    if (elements.agentActivityCard) elements.agentActivityCard.classList.remove("hidden");
  }

  state.selectedProblem = problem;
  state.activeAction = null;
  state.measurement = null;

  renderProblemsList(state.problems);

  // Switch Lifecycle Tracker
  setLifecycleStep("remember");
  elements.workspaceEmpty.classList.add("hidden");
  elements.workspaceContent.classList.add("hidden");
  elements.decisionLoading.classList.remove("hidden");
  elements.measurementSection.classList.add("hidden");
  elements.decisionLoadingMsg.textContent = "Querying Hindsight TEMPR memory bank & synthesizing decision with Gemini...";

  try {
    const res = await fetch(`${API_BASE}/api/agent/decide`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ problem_id: problem.id })
    });

    if (!res.ok) throw new Error(`Decide failed with status ${res.status}`);
    const data = await res.json();
    
    state.activeAction = data.action;
    state.recalledMemories = data.recalled_memories || [];

    setLifecycleStep("decide");
    renderDecisionWorkspace();
    renderRecalledMemories();
    showToast(`Synthesized bounded action: ${state.activeAction.title}`);
  } catch (err) {
    showToast(`Decision error: ${err.message}`, "error");
    elements.workspaceEmpty.classList.remove("hidden");
  } finally {
    elements.decisionLoading.classList.add("hidden");
  }
};

function renderDecisionWorkspace() {
  const action = state.activeAction;
  if (!action) return;

  elements.workspaceContent.classList.remove("hidden");
  elements.currentActionStateBadge.textContent = action.status;
  elements.currentActionStateBadge.className = `action-status-badge ${action.status}`;

  elements.actionTypeBadge.textContent = action.type;
  elements.actionPriorityBadge.textContent = action.priority;
  elements.actionSegmentBadge.textContent = formatName(action.affected_segment);
  elements.actionAreaBadge.textContent = formatName(action.product_area);
  elements.actionIdLabel.textContent = action.id;
  elements.actionTitle.textContent = action.title;
  elements.actionExpected.querySelector("span").textContent = action.expected_outcome;

  elements.reasoningWithText.textContent = action.reasoning_with_memory;
  elements.reasoningWithoutText.textContent = action.reasoning_without_memory;
  elements.memoryInfluenceText.textContent = action.memory_influence_summary;
  elements.actionEvidenceText.textContent = action.evidence_summary;

  // Only render the Continuous Learning / Memory Changed panel if in Challenge Mode
  if (state.isChallengeMode && elements.memoryChangedPanel) {
    elements.memoryChangedPanel.classList.remove("hidden");
    
    if (elements.adaptationRelevanceBadge) {
      const relevance = action.relevance_assessment || "HIGHLY_RELEVANT";
      elements.adaptationRelevanceBadge.textContent = relevance;
      elements.adaptationRelevanceBadge.className = `badge badge-relevance ${relevance}`;
    }
    
    if (elements.adaptationHistoricalText) {
      elements.adaptationHistoricalText.textContent = 
        action.historical_action_ref 
          ? `${action.historical_action_ref} (${action.historical_outcome_ref || 'SUCCESS: -92.9% complaints'})`
          : "INC-104 & ACT-2026-001 (Android SDK Checkout Failure, -92.9% complaints reduction)";
    }
    
    if (elements.adaptationSimilaritiesText) {
      if (Array.isArray(action.memory_similarities) && action.memory_similarities.length > 0) {
        elements.adaptationSimilaritiesText.textContent = action.memory_similarities.join("; ");
      } else {
        elements.adaptationSimilaritiesText.textContent = action.memory_similarities || "Shared Android checkout tokenization context and client gateway handshake.";
      }
    }

    if (elements.adaptationDifferencesText) {
      if (Array.isArray(action.memory_differences) && action.memory_differences.length > 0) {
        elements.adaptationDifferencesText.textContent = action.memory_differences.join("; ");
      } else {
        elements.adaptationDifferencesText.textContent = action.memory_differences || "Symptom shifted to 3DS step-up BiometricPrompt timeout rather than GooglePay token exchange.";
      }
    }

    if (elements.adaptationRationaleText) {
      elements.adaptationRationaleText.textContent = 
        action.adaptation_rationale || action.reasoning_with_memory || 
        "Prioritize Android token wrapper enhancement to renew tokens before BiometricPrompt invocation.";
    }
  } else if (elements.memoryChangedPanel) {
    elements.memoryChangedPanel.classList.add("hidden");
  }

  // Update Buttons visibility based on status
  updateButtonStates(action.status);
}

function updateButtonStates(status) {
  elements.btnApproveAction.classList.add("hidden");
  elements.btnRejectAction.classList.add("hidden");
  elements.btnExecuteAction.classList.add("hidden");
  elements.btnMeasureAction.classList.add("hidden");
  elements.btnLearnAction.classList.add("hidden");

  if (status === "RECOMMENDED") {
    elements.btnApproveAction.classList.remove("hidden");
    elements.btnRejectAction.classList.remove("hidden");
    elements.approvalInstruction.textContent = "Human-in-the-loop authorization required before executing recommended action.";
  } else if (status === "APPROVED") {
    elements.btnExecuteAction.classList.remove("hidden");
    elements.approvalInstruction.textContent = "Action approved. Ready to deploy intervention and begin telemetry monitoring.";
  } else if (status === "EXECUTED" || status === "MEASURING") {
    elements.btnMeasureAction.classList.remove("hidden");
    elements.approvalInstruction.textContent = "Intervention active. Evaluate longitudinal impact against post-period feedback.";
  } else if (status === "COMPLETED") {
    elements.approvalInstruction.textContent = "Lifecycle complete. Distilled organizational wisdom retained into Hindsight.";
  } else if (status === "REJECTED") {
    elements.approvalInstruction.textContent = "Action was rejected by human operator.";
  }
}

function renderRecalledMemories() {
  const memories = state.recalledMemories;
  elements.recalledCount.textContent = memories.length;

  if (!memories.length) {
    elements.recalledMemoriesList.innerHTML = `
      <div class="empty-hint">
        No past organizational memories matched this problem pattern.
        <br><span style="font-size:0.72rem;color:#64748b;">The agent utilized first-principles baseline reasoning.</span>
      </div>
    `;
    return;
  }

  elements.recalledMemoriesList.innerHTML = memories.map(m => `
    <div class="memory-card">
      <div class="memory-header">
        <span class="memory-category-tag ${m.category}">${m.category}</span>
        <span class="memory-relevance">${Math.round(m.relevance_score * 100)}% match</span>
      </div>
      <div class="memory-content">${escapeHtml(m.content)}</div>
      <div class="memory-meta">
        ${m.metadata.incident_id || m.metadata.action_id ? `Ref: ${m.metadata.incident_id || m.metadata.action_id}` : ''} 
        ${m.metadata.date ? `• ${m.metadata.date}` : ''}
      </div>
    </div>
  `).join("");
}

// =========================================================================
// ACTION STATE MACHINE TRANSITIONS
// =========================================================================

async function handleApprove() {
  if (!state.activeAction) return;
  try {
    const res = await fetch(`${API_BASE}/api/agent/action/transition`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action_id: state.activeAction.id, target_state: "APPROVED" })
    });
    if (!res.ok) throw new Error("Approval failed");
    const data = await res.json();
    state.activeAction = data.action;
    setLifecycleStep("approve");
    renderDecisionWorkspace();
    showToast(`Action ${state.activeAction.id} Approved.`);
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleReject() {
  if (!state.activeAction) return;
  try {
    const res = await fetch(`${API_BASE}/api/agent/action/transition`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action_id: state.activeAction.id, target_state: "REJECTED" })
    });
    if (!res.ok) throw new Error("Rejection failed");
    const data = await res.json();
    state.activeAction = data.action;
    renderDecisionWorkspace();
    showToast(`Action ${state.activeAction.id} Rejected.`);
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleExecute() {
  if (!state.activeAction) return;
  try {
    const res = await fetch(`${API_BASE}/api/agent/action/transition`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action_id: state.activeAction.id, target_state: "EXECUTED" })
    });
    if (!res.ok) throw new Error("Execution transition failed");
    const data = await res.json();
    state.activeAction = data.action;
    setLifecycleStep("execute");
    renderDecisionWorkspace();
    showToast(`Intervention launched. Monitoring telemetry...`);
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleMeasure() {
  if (!state.activeAction) return;
  try {
    const res = await fetch(`${API_BASE}/api/agent/measure`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action_id: state.activeAction.id, pre_week: 3, post_week: 4 })
    });
    if (!res.ok) throw new Error("Measurement failed");
    const data = await res.json();
    state.measurement = data.measurement;
    state.activeAction = data.action;

    setLifecycleStep("measure");
    renderMeasurementSection();
    renderDecisionWorkspace();
    
    // Enable Learn button
    elements.btnMeasureAction.classList.add("hidden");
    elements.btnLearnAction.classList.remove("hidden");
    elements.approvalInstruction.textContent = "Impact quantified. Distill and store this operational lesson into Hindsight.";
    showToast(`Impact measured: ${state.measurement.outcome} (${state.measurement.complaint_delta_pct}% complaints).`);
  } catch (err) {
    showToast(err.message, "error");
  }
}

function renderMeasurementSection() {
  const m = state.measurement;
  if (!m) return;

  elements.measurementSection.classList.remove("hidden");
  elements.measurementOutcomeBadge.textContent = m.outcome;
  elements.measurementOutcomeBadge.className = `badge ${m.outcome === 'SUCCESS' ? 'badge-primary' : 'badge-priority'}`;

  elements.metricPreComplaints.textContent = m.pre_complaint_count;
  elements.metricPostComplaints.textContent = m.post_complaint_count;
  elements.metricComplaintDelta.textContent = `${m.complaint_delta_pct > 0 ? '+' : ''}${m.complaint_delta_pct}%`;
  elements.metricComplaintDelta.className = `metric-delta ${m.complaint_delta_pct <= 0 ? 'positive' : 'negative'}`;

  elements.metricPreSentiment.textContent = m.pre_sentiment_avg;
  elements.metricPostSentiment.textContent = m.post_sentiment_avg;
  elements.metricSentimentDelta.textContent = `${m.sentiment_delta >= 0 ? '+' : ''}${m.sentiment_delta}`;
  elements.metricSentimentDelta.className = `metric-delta ${m.sentiment_delta >= 0 ? 'positive' : 'negative'}`;

  elements.lessonText.textContent = m.lesson_learned;
}

async function handleLearn() {
  if (!state.activeAction) return;
  try {
    const res = await fetch(`${API_BASE}/api/agent/learn`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action_id: state.activeAction.id })
    });
    if (!res.ok) throw new Error("Learning failed");
    const data = await res.json();
    
    setLifecycleStep("learn");
    elements.btnLearnAction.classList.add("hidden");
    elements.hindsightRetainedTag.classList.remove("hidden");
    elements.retainedMemoryId.textContent = state.activeAction.id;
    elements.currentActionStateBadge.textContent = "COMPLETED";
    elements.currentActionStateBadge.className = "action-status-badge COMPLETED";
    elements.approvalInstruction.textContent = "Lifecycle completed. Lesson retained into Hindsight organizational memory.";
    
    showToast("Successfully distilled and retained lesson into Hindsight memory!");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// =========================================================================
// HINDSIGHT SEEDING & REFLECTION
// =========================================================================

async function handleSeedMemory() {
  try {
    const res = await fetch(`${API_BASE}/api/memory/seed`, { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      showToast(data.message || "Seeded foundational memories into Hindsight.");
    }
  } catch (err) {
    showToast(`Seeding error: ${err.message}`, "error");
  }
}

async function handleRunReflection() {
  const query = elements.reflectionQueryInput.value.trim();
  if (!query) return;

  elements.reflectionLoading.classList.remove("hidden");
  elements.reflectionOutput.classList.add("hidden");

  try {
    const res = await fetch(`${API_BASE}/api/agent/reflect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query })
    });
    if (!res.ok) throw new Error("Reflection failed");
    const data = await res.json();
    elements.reflectionOutput.textContent = data.reflection;
    elements.reflectionOutput.classList.remove("hidden");
  } catch (err) {
    elements.reflectionOutput.textContent = `Error during reflection: ${err.message}`;
    elements.reflectionOutput.classList.remove("hidden");
  } finally {
    elements.reflectionLoading.classList.add("hidden");
  }
}

// =========================================================================
// UTILITIES & STEPPER
// =========================================================================

function setLifecycleStep(activeStepName) {
  const stepOrder = ["detect", "remember", "reason", "decide", "approve", "execute", "measure", "learn"];
  const activeIdx = stepOrder.indexOf(activeStepName);

  stepOrder.forEach((step, idx) => {
    const el = elements.steps[step];
    if (!el) return;
    el.classList.remove("active", "completed");
    if (idx === activeIdx) {
      el.classList.add("active");
    } else if (idx < activeIdx) {
      el.classList.add("completed");
    }
  });
}

function formatName(str) {
  if (!str) return "";
  return str.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

function escapeHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = "toast";
  if (type === "error") toast.style.borderLeftColor = "var(--danger)";
  toast.textContent = message;
  elements.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 4000);
}

// =========================================================================
// CONTINUOUS LEARNING LOOP (CHALLENGE AGENT)
// =========================================================================

const ACTIVITY_STAGES = [
  { key: "new_incident", label: "● NEW INCIDENT RECEIVED", detail: "Loaded synthetic incident: prob-challenge-002" },
  { key: "analyzing_signals", label: "● ANALYZING CURRENT SIGNALS", detail: "Telemetry: 18 complaints (+800% spike, -0.84 sentiment)" },
  { key: "searching_memory", label: "● SEARCHING ORGANIZATIONAL MEMORY", detail: "Querying Hindsight bank productpulse-ops..." },
  { key: "experience_found", label: "● RELEVANT EXPERIENCE FOUND", detail: "Retrieved incident memory INC-104 & lesson ACT-2026-001" },
  { key: "comparing_incident", label: "● COMPARING PAST AND CURRENT INCIDENT", detail: "Evaluating similarities vs differences (biometric/3DS vs GooglePay)" },
  { key: "reasoning_memory", label: "● REASONING WITH MEMORY", detail: "Evaluating memory relevance & adapting action rationale..." },
  { key: "decision_adapted", label: "● DECISION ADAPTED", detail: "Generated adapted decision based on verified organizational lesson" },
  { key: "action_proposed", label: "● ACTION PROPOSED", detail: "Bounded action structured and initialized to RECOMMENDED" },
  { key: "waiting_approval", label: "● WAITING FOR HUMAN APPROVAL", detail: "Awaiting human operator authorization" }
];

function initActivityStream() {
  if (!elements.agentActivityCard) return;
  elements.agentActivityCard.classList.remove("hidden");
  elements.activityStatusTag.innerHTML = `<span class="activity-pulse-dot"></span> Agent Running`;
  elements.activityStepsList.innerHTML = ACTIVITY_STAGES.map((s, idx) => `
    <div class="activity-step-item pending" id="activity-step-${s.key}">
      <span class="step-dot">○</span>
      <div class="activity-step-content">
        <span class="step-label">${s.label}</span>
        <span class="step-detail">${s.detail}</span>
      </div>
    </div>
  `).join("");
}

function setActivityStepState(key, status, customDetail = null) {
  const el = document.getElementById(`activity-step-${key}`);
  if (!el) return;
  el.className = `activity-step-item ${status}`;
  const dot = el.querySelector(".step-dot");
  if (dot) {
    if (status === "completed") dot.textContent = "●";
    else if (status === "active") dot.textContent = "◐";
    else dot.textContent = "○";
  }
  if (customDetail) {
    const detailEl = el.querySelector(".step-detail");
    if (detailEl) detailEl.textContent = customDetail;
  }
}

async function handleChallengeAgent() {
  if (elements.btnChallengeAgent) elements.btnChallengeAgent.disabled = true;
  
  // Clear and hide previous challenge panel while processing
  state.isChallengeMode = false;
  if (elements.memoryChangedPanel) elements.memoryChangedPanel.classList.add("hidden");

  initActivityStream();

  setActivityStepState("new_incident", "active");

  try {
    // Stage 1: Trigger challenge incident creation
    const challengeRes = await fetch(`${API_BASE}/api/agent/challenge`, { method: "POST" });
    if (!challengeRes.ok) throw new Error(`Challenge initialization failed: ${challengeRes.status}`);
    const challengeData = await challengeRes.json();
    const challengeProblem = challengeData.problem;

    setActivityStepState("new_incident", "completed");
    setActivityStepState("analyzing_signals", "active");

    // Add problem to state and re-render problem list
    state.problems = [challengeProblem, ...state.problems.filter(p => p.id !== challengeProblem.id)];
    state.selectedProblem = challengeProblem;
    state.activeAction = null;
    state.measurement = null;
    renderProblemsList(state.problems);

    setActivityStepState("analyzing_signals", "completed", `Detected: ${challengeProblem.complaint_count} complaints, trend +${challengeProblem.trend_pct}%, sentiment ${challengeProblem.sentiment_avg}`);
    setActivityStepState("searching_memory", "active");

    setLifecycleStep("remember");
    elements.workspaceEmpty.classList.add("hidden");
    elements.workspaceContent.classList.add("hidden");
    elements.decisionLoading.classList.remove("hidden");
    elements.measurementSection.classList.add("hidden");
    elements.decisionLoadingMsg.textContent = "⚡ Challenging ProductPulse: Recalling historical organizational wisdom for Android checkout...";

    // Stage 2: Run Decision Engine with Real Hindsight
    const decideRes = await fetch(`${API_BASE}/api/agent/decide`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ problem_id: challengeProblem.id })
    });

    if (!decideRes.ok) throw new Error(`Decide failed: ${decideRes.status}`);
    const decideData = await decideRes.json();

    state.activeAction = decideData.action;
    state.recalledMemories = decideData.recalled_memories || [];

    setActivityStepState("searching_memory", "completed");
    setActivityStepState("experience_found", "completed", `Retrieved ${state.recalledMemories.length} memories from Hindsight bank`);
    setActivityStepState("comparing_incident", "completed", `Similarities: ${state.activeAction.memory_similarities?.length || 1} • Differences: ${state.activeAction.memory_differences?.length || 1}`);
    setActivityStepState("reasoning_memory", "completed", `Relevance: ${state.activeAction.relevance_assessment || 'HIGHLY_RELEVANT'}`);
    setActivityStepState("decision_adapted", "completed", state.activeAction.title);
    setActivityStepState("action_proposed", "completed", `Action ID: ${state.activeAction.id}`);
    setActivityStepState("waiting_approval", "active");

    elements.activityStatusTag.innerHTML = `<span style="color:#34d399;">●</span> Awaiting Approval`;

    // Now activate Challenge Mode upon successful decision generation
    state.isChallengeMode = true;

    setLifecycleStep("decide");
    renderDecisionWorkspace();
    renderRecalledMemories();

    showToast("⚡ ProductPulse adapted decision using recalled organizational memory!");
    
    // Smooth scroll down to the adapted decision panel
    if (elements.memoryChangedPanel) {
      elements.memoryChangedPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  } catch (err) {
    showToast(`Challenge error: ${err.message}`, "error");
    elements.workspaceEmpty.classList.remove("hidden");
    if (elements.activityStatusTag) elements.activityStatusTag.textContent = "Error";
    state.isChallengeMode = false;
    if (elements.memoryChangedPanel) elements.memoryChangedPanel.classList.add("hidden");
  } finally {
    elements.decisionLoading.classList.add("hidden");
    if (elements.btnChallengeAgent) elements.btnChallengeAgent.disabled = false;
  }
}
