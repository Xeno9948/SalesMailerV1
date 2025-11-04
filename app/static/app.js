const state = {
  brands: [],
  features: [],
  templates: [],
  campaigns: [],
  brandFeatures: {},
  campaignFeatures: {},
};

const selectors = {
  brandForm: document.getElementById("brandForm"),
  featureForm: document.getElementById("featureForm"),
  brandFeatureForm: document.getElementById("brandFeatureForm"),
  templateForm: document.getElementById("templateForm"),
  campaignForm: document.getElementById("campaignForm"),
  campaignFeatureForm: document.getElementById("campaignFeatureForm"),
  leadForm: document.getElementById("leadForm"),
  brandList: document.getElementById("brandList"),
  featureList: document.getElementById("featureList"),
  brandFeatureList: document.getElementById("brandFeatureList"),
  templateList: document.getElementById("templateList"),
  campaignList: document.getElementById("campaignList"),
  previewArticle: document.getElementById("preview"),
};

async function api(path, { method = "GET", body } = {}) {
  const options = { method, headers: { "Content-Type": "application/json" } };
  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(path, options);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed with ${response.status}`);
  }

  if (response.status === 204) {
    return null;
  }
  return response.json();
}

function resolveKey(item, key) {
  if (typeof key === "function") {
    return key(item);
  }
  return item[key];
}

function setSelectOptions(select, options, { valueKey = "id", labelKey = "name", placeholder } = {}) {
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
  options.forEach((item) => {
    const option = document.createElement("option");
    option.value = resolveKey(item, valueKey);
    option.textContent = resolveKey(item, labelKey);
    select.appendChild(option);
  });
}

function renderBrandList() {
  const list = selectors.brandList;
  list.innerHTML = "";
  state.brands.forEach((brand) => {
    const card = document.createElement("article");
    card.className = "item-card";
    card.innerHTML = `
      <h3>${brand.name} <span class="meta">(${brand.slug})</span></h3>
      <div class="meta">Sender: ${brand.sender_name || "-"} &lt;${brand.sender_email || "n/a"}&gt;</div>
      <div class="meta">Default subject: ${brand.default_subject || "-"}</div>
      <div class="meta">Tone: ${brand.default_tone || "-"}</div>
    `;
    list.appendChild(card);
  });

  const brandSelects = [
    selectors.brandFeatureForm?.elements.namedItem("brand_id"),
    selectors.templateForm?.elements.namedItem("brand_id"),
    selectors.campaignForm?.elements.namedItem("brand_id"),
  ];
  brandSelects.forEach((select) =>
    setSelectOptions(select, state.brands, {
      placeholder: state.brands.length ? "Choose a brand" : "Add a brand first",
    })
  );

  const slugSelect = selectors.leadForm?.elements.namedItem("brand_slug");
  setSelectOptions(slugSelect, state.brands, {
    valueKey: "slug",
    labelKey: "name",
    placeholder: state.brands.length ? "Select a brand" : "Add a brand first",
  });
}

function renderFeatureList() {
  const list = selectors.featureList;
  list.innerHTML = "";
  state.features.forEach((feature) => {
    const card = document.createElement("article");
    card.className = "item-card";
    card.innerHTML = `
      <h3>${feature.name}</h3>
      <div class="meta">${feature.short_description}</div>
    `;
    list.appendChild(card);
  });

  const featureSelect = selectors.brandFeatureForm?.elements.namedItem("feature_id");
  setSelectOptions(featureSelect, state.features, {
    placeholder: state.features.length ? "Choose a feature" : "Add a feature first",
  });
}

function renderBrandFeatureList() {
  const list = selectors.brandFeatureList;
  list.innerHTML = "";
  const entries = Object.entries(state.brandFeatures);
  if (!entries.length) {
    list.innerHTML = "<p class=\"meta\">No brand features yet.</p>";
    return;
  }

  entries.forEach(([brandId, features]) => {
    const brand = state.brands.find((b) => b.id === Number(brandId));
    if (!brand) return;
    const wrapper = document.createElement("div");
    wrapper.className = "item-card";
    const lines = features
      .map((bf) => {
        const label = bf.asset_label ? ` (${bf.asset_label})` : "";
        const cta = bf.cta_text ? ` – ${bf.cta_text}` : "";
        return `<li>${bf.feature.name}${label}${cta}</li>`;
      })
      .join("");
    wrapper.innerHTML = `
      <h3>${brand.name}</h3>
      <ul>${lines || "<li>No linked features yet.</li>"}</ul>
    `;
    list.appendChild(wrapper);
  });
}

function renderTemplateList() {
  const list = selectors.templateList;
  list.innerHTML = "";
  state.templates.forEach((template) => {
    const brand = state.brands.find((b) => b.id === template.brand_id);
    const card = document.createElement("article");
    card.className = "item-card";
    card.innerHTML = `
      <h3>${template.name} <span class="meta">for ${brand ? brand.name : "Unknown"}</span></h3>
      <div class="meta">Subject: ${template.subject_template || "(default subject)"}</div>
      <div class="meta">Default: ${template.is_default ? "Yes" : "No"}</div>
    `;
    list.appendChild(card);
  });
}

function renderCampaignList() {
  const list = selectors.campaignList;
  list.innerHTML = "";
  state.campaigns.forEach((campaign) => {
    const brand = state.brands.find((b) => b.id === campaign.brand_id);
    const features = state.campaignFeatures[campaign.id] || [];
    const card = document.createElement("article");
    card.className = "item-card";
    const featureItems = features
      .map((cf) => `<li>${cf.brand_feature.feature.name} – ${cf.highlight_text || "(default copy)"}</li>`)
      .join("");
    card.innerHTML = `
      <h3>${campaign.name} <span class="meta">for ${brand ? brand.name : "Unknown"}</span></h3>
      <div class="meta">${campaign.description || "No description"}</div>
      <div class="meta">Tone: ${campaign.tone_override || brand?.default_tone || "Brand default"}</div>
      <div class="meta">Status: ${campaign.is_active ? "Active" : "Draft"}</div>
      <ul>${featureItems || "<li>No features yet.</li>"}</ul>
    `;
    list.appendChild(card);
  });

  const campaignSelect = selectors.campaignFeatureForm?.elements.namedItem("campaign_id");
  setSelectOptions(campaignSelect, state.campaigns, {
    labelKey: "name",
    placeholder: state.campaigns.length ? "Choose a campaign" : "Create a campaign first",
  });
}

function renderCampaignFeatureSelect() {
  const form = selectors.campaignFeatureForm;
  if (!form) return;
  const campaignId = Number(form.elements.namedItem("campaign_id").value);
  if (!campaignId) {
    setSelectOptions(form.elements.namedItem("brand_feature_id"), [], {
      placeholder: "Select a campaign first",
    });
    return;
  }
  const campaign = state.campaigns.find((c) => c.id === campaignId);
  if (!campaign) return;
  const brandFeatureOptions = state.brandFeatures[campaign.brand_id] || [];
  if (!brandFeatureOptions.length) {
    setSelectOptions(form.elements.namedItem("brand_feature_id"), [], {
      placeholder: "Link brand features before adding",
    });
    return;
  }
  setSelectOptions(form.elements.namedItem("brand_feature_id"), brandFeatureOptions, {
    valueKey: "id",
    labelKey: (bf) => `${bf.feature.name}${bf.asset_label ? " (" + bf.asset_label + ")" : ""}`,
    placeholder: "Choose a brand feature",
  });
}

function resetForm(form) {
  if (!form) return;
  form.reset();
  if (form.elements[0] && form.elements[0].tagName === "SELECT") {
    const event = new Event("change");
    form.elements[0].dispatchEvent(event);
  }
}

function displayPreview({ subject, html_body: htmlBody, tone }) {
  const article = selectors.previewArticle;
  const emptyState = article.querySelector(".empty");
  if (emptyState) {
    emptyState.remove();
  }
  const meta = article.querySelector(".preview-meta");
  meta.innerHTML = `
    <div><strong>Subject:</strong> ${subject}</div>
    <div><strong>Tone:</strong> ${tone || "Brand default"}</div>
  `;
  const frame = article.querySelector(".preview-frame");
  if (!frame) return;
  const doc = frame.contentDocument || frame.contentWindow.document;
  doc.open();
  doc.write(htmlBody);
  doc.close();
}

async function loadBrands() {
  state.brands = await api("/brands/");
  renderBrandList();
  await loadBrandFeatures();
  renderCampaignFeatureSelect();
}

async function loadFeatures() {
  state.features = await api("/features/");
  renderFeatureList();
}

async function loadBrandFeatures() {
  const entries = await Promise.all(
    state.brands.map(async (brand) => {
      const items = await api(`/features/brand/${brand.id}`);
      return [brand.id, items];
    })
  );
  state.brandFeatures = Object.fromEntries(entries);
  renderBrandFeatureList();
  renderCampaignFeatureSelect();
}

async function loadTemplates() {
  state.templates = await api("/templates/");
  renderTemplateList();
}

async function loadCampaigns() {
  state.campaigns = await api("/campaigns/");
  renderCampaignList();
  const featurePairs = await Promise.all(
    state.campaigns.map(async (campaign) => {
      const features = await api(`/campaigns/${campaign.id}/features`);
      return [campaign.id, features];
    })
  );
  state.campaignFeatures = Object.fromEntries(featurePairs);
  renderCampaignList();
  renderCampaignFeatureSelect();
}

async function initialize() {
  await Promise.all([loadBrands(), loadFeatures(), loadTemplates(), loadCampaigns()]);
}

document.addEventListener("DOMContentLoaded", () => {
  initialize().catch((error) => console.error(error));

  selectors.brandForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.target).entries());
    try {
      await api("/brands/", { method: "POST", body: data });
      await loadBrands();
      resetForm(event.target);
    } catch (error) {
      alert(error.message);
    }
  });

  selectors.featureForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.target).entries());
    try {
      await api("/features/", { method: "POST", body: data });
      await loadFeatures();
      resetForm(event.target);
    } catch (error) {
      alert(error.message);
    }
  });

  selectors.brandFeatureForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());
    data.brand_id = Number(data.brand_id);
    data.feature_id = Number(data.feature_id);
    try {
      await api("/features/brand", { method: "POST", body: data });
      await loadBrandFeatures();
      resetForm(event.target);
    } catch (error) {
      alert(error.message);
    }
  });

  selectors.templateForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());
    data.brand_id = Number(data.brand_id);
    data.is_default = formData.get("is_default") === "on";
    try {
      await api("/templates/", { method: "POST", body: data });
      await loadTemplates();
      resetForm(event.target);
    } catch (error) {
      alert(error.message);
    }
  });

  selectors.campaignForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());
    data.brand_id = Number(data.brand_id);
    data.is_active = formData.get("is_active") === "on";
    try {
      await api("/campaigns/", { method: "POST", body: data });
      await loadCampaigns();
      resetForm(event.target);
    } catch (error) {
      alert(error.message);
    }
  });

  selectors.campaignFeatureForm?.elements
    ?.namedItem("campaign_id")
    ?.addEventListener("change", renderCampaignFeatureSelect);

  selectors.campaignFeatureForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());
    data.campaign_id = Number(data.campaign_id);
    data.brand_feature_id = Number(data.brand_feature_id);
    data.sort_order = Number(data.sort_order || 0);
    try {
      await api(`/campaigns/${data.campaign_id}/features`, { method: "POST", body: data });
      await loadCampaigns();
      resetForm(event.target);
    } catch (error) {
      alert(error.message);
    }
  });

  selectors.leadForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.target).entries());
    try {
      const lead = await api("/leads/", { method: "POST", body: data });
      const emails = await api(`/leads/${lead.id}/emails`);
      if (emails.length) {
        const latest = emails[emails.length - 1];
        const brand = state.brands.find((b) => b.id === lead.brand_id);
        const campaign = state.campaigns.find((c) => c.id === latest.campaign_id);
        const tone = latest.metadata?.tone || campaign?.tone_override || brand?.default_tone;
        displayPreview({ subject: latest.subject, html_body: latest.html_body, tone });
      }
      resetForm(event.target);
    } catch (error) {
      alert(error.message);
    }
  });
});
