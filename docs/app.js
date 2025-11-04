const STORAGE_KEY = "salesmailer.portal.v1";
const EMPTY_STATE = Object.freeze({
  brands: [],
  features: [],
  brandFeatures: [],
  templates: [],
  campaigns: [],
  leads: [],
});

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return clone(EMPTY_STATE);
    const parsed = JSON.parse(raw);
    return { ...clone(EMPTY_STATE), ...parsed };
  } catch (error) {
    console.warn("Unable to load saved workspace; starting fresh.", error);
    return clone(EMPTY_STATE);
  }
}

function persistState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function createId(prefix) {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${prefix}-${Math.random().toString(36).slice(2)}-${Date.now().toString(36)}`;
}

function getPath(obj, path) {
  return path.split(".").reduce((value, key) => (value ? value[key] : undefined), obj);
}

function interpolate(template, context) {
  if (!template) return "";
  return template.replace(/{{\s*([\w.]+)\s*}}/g, (_, expression) => {
    const value = getPath(context, expression.trim());
    return value != null ? value : "";
  });
}

function formatEmailPreview({ brand, template, lead, campaign, features }) {
  if (!brand || !template || !lead) {
    return {
      subject: "Select a brand, lead, and template to render a preview.",
      body: "",
    };
  }

  const context = {
    brand,
    lead,
    campaign,
    feature: features[0] || {},
    features,
  };

  const subjectTemplate = template.subject?.trim() || brand.defaultSubject || `${brand.name} confirmation`;
  const htmlTemplate = template.html?.trim() ||
    `<p>Hi {{ lead.contact || lead.company }},</p>
     <p>Thanks for connecting with {{ brand.name }}. We'll follow up shortly with tailored resources.</p>`;

  const subject = interpolate(subjectTemplate, context) || subjectTemplate;
  const baseBody = interpolate(htmlTemplate, context);
  const highlightList = features.length
    ? `<h4>Highlights selected for this send:</h4>
       <ul>${features
         .map((item) => {
           const lines = [
             `<strong>${item.feature.name}</strong>`,
             item.feature.shortDescription && `<span>${item.feature.shortDescription}</span>`,
             item.ctaText && item.ctaUrl && `<a href="${item.ctaUrl}" target="_blank" rel="noopener">${item.ctaText}</a>`,
             item.ctaText && !item.ctaUrl && `<span>${item.ctaText}</span>`,
           ].filter(Boolean);
           return `<li>${lines.join("<br/>")}</li>`;
         })
         .join("")}</ul>`
    : "";

  const campaignSummary = campaign
    ? `<p><em>Campaign tone:</em> ${campaign.tone || "Custom"} – ${campaign.goal || "Conversion"}</p>`
    : "";

  return {
    subject,
    body: `${baseBody}${highlightList}${campaignSummary}`,
  };
}

const state = loadState();

const selectors = {
  brandForm: document.getElementById("brandForm"),
  brandList: document.getElementById("brandList"),
  featureForm: document.getElementById("featureForm"),
  featureList: document.getElementById("featureList"),
  brandFeatureForm: document.getElementById("brandFeatureForm"),
  brandFeatureList: document.getElementById("brandFeatureList"),
  templateForm: document.getElementById("templateForm"),
  templateList: document.getElementById("templateList"),
  campaignForm: document.getElementById("campaignForm"),
  campaignList: document.getElementById("campaignList"),
  leadForm: document.getElementById("leadForm"),
  leadList: document.getElementById("leadList"),
  previewForm: document.getElementById("previewForm"),
  previewSubject: document.getElementById("previewSubject"),
  previewBody: document.getElementById("previewBody"),
  previewFeatures: document.getElementById("previewFeatures"),
  exportButton: document.getElementById("exportButton"),
  importInput: document.getElementById("importInput"),
  resetButton: document.getElementById("resetButton"),
};

function clearForm(form) {
  form?.reset();
  const selectElements = form?.querySelectorAll("select");
  selectElements?.forEach((select) => {
    select.selectedIndex = -1;
  });
}

function handleBrandSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const slug = data.get("slug").trim();
  if (state.brands.some((brand) => brand.slug === slug)) {
    alert("A brand with this slug already exists.");
    return;
  }
  state.brands.push({
    id: createId("brand"),
    name: data.get("name").trim(),
    slug,
    senderName: data.get("senderName").trim(),
    senderEmail: data.get("senderEmail").trim(),
    defaultSubject: data.get("defaultSubject").trim(),
    defaultTone: data.get("defaultTone").trim(),
  });
  persistState();
  clearForm(form);
  renderAll();
}

function handleFeatureSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  state.features.push({
    id: createId("feature"),
    name: data.get("name").trim(),
    shortDescription: data.get("shortDescription").trim(),
    longDescription: data.get("longDescription").trim(),
    assetLabel: data.get("assetLabel").trim(),
    assetUrl: data.get("assetUrl").trim(),
  });
  persistState();
  clearForm(form);
  renderAll();
}

function handleBrandFeatureSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const brandId = data.get("brandId");
  const featureId = data.get("featureId");
  if (state.brandFeatures.some((item) => item.brandId === brandId && item.featureId === featureId)) {
    alert("This feature is already attached to the selected brand.");
    return;
  }
  state.brandFeatures.push({
    id: createId("brand-feature"),
    brandId,
    featureId,
    ctaText: data.get("ctaText").trim(),
    ctaUrl: data.get("ctaUrl").trim(),
  });
  persistState();
  clearForm(form);
  renderAll();
}

function handleTemplateSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  state.templates.push({
    id: createId("template"),
    brandId: data.get("brandId"),
    name: data.get("name").trim(),
    subject: data.get("subject").trim(),
    html: data.get("html").trim(),
  });
  persistState();
  clearForm(form);
  renderAll();
}

function handleCampaignSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  state.campaigns.push({
    id: createId("campaign"),
    brandId: data.get("brandId"),
    name: data.get("name").trim(),
    tone: data.get("tone").trim(),
    goal: data.get("goal").trim(),
  });
  persistState();
  clearForm(form);
  renderAll();
}

function handleLeadSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  state.leads.push({
    id: createId("lead"),
    brandSlug: data.get("brandSlug"),
    company: data.get("company").trim(),
    contact: data.get("contact").trim(),
    email: data.get("email").trim(),
    notes: data.get("notes").trim(),
  });
  persistState();
  clearForm(form);
  renderAll();
}

function removeBrand(id) {
  const brand = state.brands.find((item) => item.id === id);
  state.brands = state.brands.filter((item) => item.id !== id);
  state.templates = state.templates.filter((item) => item.brandId !== id);
  state.campaigns = state.campaigns.filter((item) => item.brandId !== id);
  state.brandFeatures = state.brandFeatures.filter((item) => item.brandId !== id);
  if (brand) {
    state.leads = state.leads.filter((lead) => lead.brandSlug !== brand.slug);
  }
  persistState();
  renderAll();
}

function removeFeature(id) {
  state.features = state.features.filter((item) => item.id !== id);
  state.brandFeatures = state.brandFeatures.filter((item) => item.featureId !== id);
  persistState();
  renderAll();
}

function removeBrandFeature(id) {
  state.brandFeatures = state.brandFeatures.filter((item) => item.id !== id);
  persistState();
  renderAll();
}

function removeTemplate(id) {
  state.templates = state.templates.filter((item) => item.id !== id);
  persistState();
  renderAll();
}

function removeCampaign(id) {
  state.campaigns = state.campaigns.filter((item) => item.id !== id);
  persistState();
  renderAll();
}

function removeLead(id) {
  state.leads = state.leads.filter((item) => item.id !== id);
  persistState();
  renderAll();
}

function createDeleteButton(label, handler) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.className = "ghost";
  button.addEventListener("click", handler);
  return button;
}

function renderBrandList() {
  const container = selectors.brandList;
  container.innerHTML = "";
  if (!state.brands.length) {
    container.innerHTML = '<p class="meta">Add your first brand to get started.</p>';
    return;
  }
  state.brands.forEach((brand) => {
    const card = document.createElement("article");
    card.className = "item-card";
    card.innerHTML = `
      <h3>${brand.name} <span class="meta">(${brand.slug})</span></h3>
      <div class="meta">Sender: ${brand.senderName || "—"} &lt;${brand.senderEmail || "n/a"}&gt;</div>
      <div class="meta">Default subject: ${brand.defaultSubject || "—"}</div>
      <div class="meta">Tone: ${brand.defaultTone || "Custom"}</div>
    `;
    const actions = document.createElement("div");
    actions.appendChild(createDeleteButton("Remove", () => removeBrand(brand.id)));
    card.appendChild(actions);
    container.appendChild(card);
  });
}

function renderFeatureList() {
  const container = selectors.featureList;
  container.innerHTML = "";
  if (!state.features.length) {
    container.innerHTML = '<p class="meta">Store reusable highlights for your campaigns.</p>';
    return;
  }
  state.features.forEach((feature) => {
    const card = document.createElement("article");
    card.className = "item-card";
    const assetLine = feature.assetUrl
      ? `<div class="meta">${feature.assetLabel || "Asset"}: <a href="${feature.assetUrl}" target="_blank" rel="noopener">${feature.assetUrl}</a></div>`
      : "";
    card.innerHTML = `
      <h3>${feature.name}</h3>
      <div class="meta">${feature.shortDescription || "No highlight copy yet."}</div>
      ${feature.longDescription ? `<p>${feature.longDescription}</p>` : ""}
      ${assetLine}
    `;
    const actions = document.createElement("div");
    actions.appendChild(createDeleteButton("Remove", () => removeFeature(feature.id)));
    card.appendChild(actions);
    container.appendChild(card);
  });
}

function renderBrandFeatureList() {
  const container = selectors.brandFeatureList;
  container.innerHTML = "";
  if (!state.brandFeatures.length) {
    container.innerHTML = '<p class="meta">Attach features to each brand to make them selectable in previews.</p>';
    return;
  }
  const grouped = state.brandFeatures.reduce((acc, item) => {
    acc[item.brandId] = acc[item.brandId] || [];
    acc[item.brandId].push(item);
    return acc;
  }, {});
  Object.entries(grouped).forEach(([brandId, items]) => {
    const brand = state.brands.find((b) => b.id === brandId);
    const card = document.createElement("article");
    card.className = "item-card";
    card.innerHTML = `<h3>${brand ? brand.name : "Unknown brand"}</h3>`;
    const list = document.createElement("ul");
    items.forEach((item) => {
      const feature = state.features.find((f) => f.id === item.featureId);
      const li = document.createElement("li");
      li.innerHTML = `
        <strong>${feature ? feature.name : "Unknown feature"}</strong>
        ${item.ctaText ? ` – ${item.ctaText}` : ""}
        ${item.ctaUrl ? ` (<a href="${item.ctaUrl}" target="_blank" rel="noopener">link</a>)` : ""}
      `;
      li.appendChild(createDeleteButton("Remove", () => removeBrandFeature(item.id)));
      list.appendChild(li);
    });
    card.appendChild(list);
    container.appendChild(card);
  });
}

function renderTemplateList() {
  const container = selectors.templateList;
  container.innerHTML = "";
  if (!state.templates.length) {
    container.innerHTML = '<p class="meta">Draft brand-specific HTML templates for your outreach.</p>';
    return;
  }
  state.templates.forEach((template) => {
    const brand = state.brands.find((b) => b.id === template.brandId);
    const card = document.createElement("article");
    card.className = "item-card";
    card.innerHTML = `
      <h3>${template.name} <span class="meta">for ${brand ? brand.name : "Unknown brand"}</span></h3>
      <div class="meta">Subject: ${template.subject || brand?.defaultSubject || "—"}</div>
      <pre class="meta" style="white-space: pre-wrap;">${template.html || "No HTML provided yet."}</pre>
    `;
    const actions = document.createElement("div");
    actions.appendChild(createDeleteButton("Remove", () => removeTemplate(template.id)));
    card.appendChild(actions);
    container.appendChild(card);
  });
}

function renderCampaignList() {
  const container = selectors.campaignList;
  container.innerHTML = "";
  if (!state.campaigns.length) {
    container.innerHTML = '<p class="meta">Capture tone and goals for this month\'s messaging.</p>';
    return;
  }
  state.campaigns.forEach((campaign) => {
    const brand = state.brands.find((b) => b.id === campaign.brandId);
    const card = document.createElement("article");
    card.className = "item-card";
    card.innerHTML = `
      <h3>${campaign.name}</h3>
      <div class="meta">Brand: ${brand ? brand.name : "Unknown brand"}</div>
      <div class="meta">Tone: ${campaign.tone || brand?.defaultTone || "Custom"}</div>
      <div class="meta">Goal: ${campaign.goal || "Not specified"}</div>
    `;
    const actions = document.createElement("div");
    actions.appendChild(createDeleteButton("Remove", () => removeCampaign(campaign.id)));
    card.appendChild(actions);
    container.appendChild(card);
  });
}

function renderLeadList() {
  const container = selectors.leadList;
  container.innerHTML = "";
  if (!state.leads.length) {
    container.innerHTML = '<p class="meta">Leads will appear here once added.</p>';
    return;
  }
  state.leads.forEach((lead) => {
    const brand = state.brands.find((b) => b.slug === lead.brandSlug);
    const card = document.createElement("article");
    card.className = "item-card";
    card.innerHTML = `
      <h3>${lead.company}</h3>
      <div class="meta">Brand: ${brand ? brand.name : lead.brandSlug}</div>
      <div class="meta">Contact: ${lead.contact || "Unknown"} (${lead.email || "n/a"})</div>
      ${lead.notes ? `<p>${lead.notes}</p>` : ""}
    `;
    const actions = document.createElement("div");
    actions.appendChild(createDeleteButton("Remove", () => removeLead(lead.id)));
    card.appendChild(actions);
    container.appendChild(card);
  });
}

function setSelectOptions(select, items, { valueKey = "id", labelKey = "name", placeholder } = {}) {
  if (!select) return;
  select.innerHTML = "";
  if (placeholder) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = placeholder;
    option.disabled = true;
    option.selected = true;
    select.appendChild(option);
  }
  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = item[valueKey];
    option.textContent = item[labelKey] || item[valueKey];
    select.appendChild(option);
  });
}

function renderFormOptions() {
  const brandOptions = state.brands.map((brand) => ({
    id: brand.id,
    name: brand.name,
  }));
  const brandSlugOptions = state.brands.map((brand) => ({
    id: brand.slug,
    name: brand.name,
  }));
  const featureOptions = state.features.map((feature) => ({
    id: feature.id,
    name: feature.name,
  }));
  setSelectOptions(document.getElementById("brandSelect"), brandOptions, {
    placeholder: brandOptions.length ? "Choose a brand" : "Add a brand first",
  });
  setSelectOptions(document.getElementById("featureSelect"), featureOptions, {
    placeholder: featureOptions.length ? "Choose a feature" : "Add a feature first",
  });
  setSelectOptions(document.getElementById("templateBrand"), brandOptions, {
    placeholder: brandOptions.length ? "Brand" : "Add a brand first",
  });
  setSelectOptions(document.getElementById("campaignBrand"), brandOptions, {
    placeholder: brandOptions.length ? "Brand" : "Add a brand first",
  });
  setSelectOptions(document.getElementById("leadBrand"), brandSlugOptions, {
    placeholder: brandSlugOptions.length ? "Brand" : "Add a brand first",
    valueKey: "id",
  });
}

function renderPreviewSelectors() {
  const brandSelect = document.getElementById("previewBrand");
  const templateSelect = document.getElementById("previewTemplate");
  const campaignSelect = document.getElementById("previewCampaign");
  const leadSelect = document.getElementById("previewLead");
  const featureSelect = selectors.previewFeatures;

  const previousSelections = {
    brand: brandSelect?.value,
    template: templateSelect?.value,
    campaign: campaignSelect?.value,
    lead: leadSelect?.value,
    features: new Set(Array.from(featureSelect?.selectedOptions || []).map((option) => option.value)),
  };

  setSelectOptions(brandSelect, state.brands, { placeholder: "Brand" });
  if (previousSelections.brand && state.brands.some((item) => item.id === previousSelections.brand)) {
    brandSelect.value = previousSelections.brand;
  }

  const selectedBrandId = brandSelect.value;
  const brand = state.brands.find((item) => item.id === selectedBrandId);

  const brandTemplates = selectedBrandId
    ? state.templates.filter((item) => item.brandId === selectedBrandId)
    : state.templates;
  const brandCampaigns = selectedBrandId
    ? state.campaigns.filter((item) => item.brandId === selectedBrandId)
    : state.campaigns;
  const brandFeatures = selectedBrandId
    ? state.brandFeatures.filter((item) => item.brandId === selectedBrandId)
    : state.brandFeatures;
  const brandLeads = brand
    ? state.leads.filter((item) => item.brandSlug === brand.slug)
    : state.leads;

  setSelectOptions(templateSelect, brandTemplates, { placeholder: brandTemplates.length ? "Template" : "No templates" });
  if (previousSelections.template && brandTemplates.some((item) => item.id === previousSelections.template)) {
    templateSelect.value = previousSelections.template;
  }

  setSelectOptions(campaignSelect, brandCampaigns, { placeholder: brandCampaigns.length ? "Campaign" : "Optional" });
  if (previousSelections.campaign && brandCampaigns.some((item) => item.id === previousSelections.campaign)) {
    campaignSelect.value = previousSelections.campaign;
  }

  setSelectOptions(leadSelect, brandLeads, {
    placeholder: brandLeads.length ? "Lead" : "Add a lead",
    labelKey: "company",
  });
  if (previousSelections.lead && brandLeads.some((item) => item.id === previousSelections.lead)) {
    leadSelect.value = previousSelections.lead;
  }

  featureSelect.innerHTML = "";
  brandFeatures.forEach((item) => {
    const feature = state.features.find((f) => f.id === item.featureId);
    if (!feature) return;
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = feature.name;
    if (previousSelections.features.has(item.id)) {
      option.selected = true;
    }
    featureSelect.appendChild(option);
  });
}

function updatePreview() {
  const brandId = document.getElementById("previewBrand").value;
  const templateId = document.getElementById("previewTemplate").value;
  const leadId = document.getElementById("previewLead").value;
  const campaignId = document.getElementById("previewCampaign").value;
  const featureIds = Array.from(selectors.previewFeatures.selectedOptions).map((option) => option.value);

  const brand = state.brands.find((item) => item.id === brandId);
  const template = state.templates.find((item) => item.id === templateId);
  const lead = state.leads.find((item) => item.id === leadId);
  const campaign = state.campaigns.find((item) => item.id === campaignId);
  const features = featureIds
    .map((id) => state.brandFeatures.find((item) => item.id === id))
    .filter(Boolean)
    .map((item) => ({
      ...item,
      feature: state.features.find((feature) => feature.id === item.featureId) || {},
    }));

  const preview = formatEmailPreview({ brand, template, lead, campaign, features });
  selectors.previewSubject.textContent = preview.subject;
  selectors.previewBody.innerHTML = preview.body;
}

function renderAll() {
  renderBrandList();
  renderFeatureList();
  renderBrandFeatureList();
  renderTemplateList();
  renderCampaignList();
  renderLeadList();
  renderFormOptions();
  renderPreviewSelectors();
  updatePreview();
}

function exportState() {
  const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `salesmailer-workspace-${new Date().toISOString().slice(0, 10)}.json`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

function importState(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (event) => {
    try {
      const imported = JSON.parse(event.target.result);
      Object.keys(EMPTY_STATE).forEach((key) => {
        state[key] = Array.isArray(imported[key]) ? imported[key] : [];
      });
      persistState();
      renderAll();
    } catch (error) {
      alert("Unable to import file. Ensure it's a SalesMailer export.");
      console.error(error);
    }
  };
  reader.readAsText(file);
}

function resetWorkspace() {
  if (!confirm("This will remove all brands, features, templates, campaigns, and leads stored in your browser. Continue?")) {
    return;
  }
  Object.keys(EMPTY_STATE).forEach((key) => {
    state[key] = [];
  });
  persistState();
  renderAll();
}

selectors.brandForm?.addEventListener("submit", handleBrandSubmit);
selectors.featureForm?.addEventListener("submit", handleFeatureSubmit);
selectors.brandFeatureForm?.addEventListener("submit", handleBrandFeatureSubmit);
selectors.templateForm?.addEventListener("submit", handleTemplateSubmit);
selectors.campaignForm?.addEventListener("submit", handleCampaignSubmit);
selectors.leadForm?.addEventListener("submit", handleLeadSubmit);

selectors.previewForm?.addEventListener("change", (event) => {
  if (event.target && ["previewBrand", "previewTemplate", "previewLead", "previewCampaign"].includes(event.target.id)) {
    if (event.target.id === "previewBrand") {
      renderPreviewSelectors();
    }
    updatePreview();
  }
});
selectors.previewFeatures?.addEventListener("change", updatePreview);

selectors.exportButton?.addEventListener("click", exportState);
selectors.importInput?.addEventListener("change", (event) => importState(event.target.files[0]));
selectors.resetButton?.addEventListener("click", resetWorkspace);

document.getElementById("previewBrand")?.addEventListener("change", () => {
  renderPreviewSelectors();
  updatePreview();
});

renderAll();
