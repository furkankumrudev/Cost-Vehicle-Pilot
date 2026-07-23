const marketData = [
  {
    brand: "Volkswagen",
    series: "Golf",
    models: ["Tum paketler", "1.0 TSI", "1.5 TSI", "2.0 TDI"],
    basePrice: 1340000,
    median: 1395000,
    count: 312,
    cleanCount: 74,
    cities: { Istanbul: 92, Ankara: 48, Izmir: 36, Bursa: 28, Antalya: 22 },
  },
  {
    brand: "BMW",
    series: "2 Serisi",
    models: ["Tum paketler", "216d", "218i", "220i", "M Sport"],
    basePrice: 2260000,
    median: 2315000,
    count: 118,
    cleanCount: 27,
    cities: { Istanbul: 42, Ankara: 18, Izmir: 13, Bursa: 10, Antalya: 9 },
  },
  {
    brand: "Mercedes-Benz",
    series: "C Serisi",
    models: ["Tum paketler", "C 180", "C 200", "AMG", "Avantgarde"],
    basePrice: 2890000,
    median: 3025000,
    count: 244,
    cleanCount: 51,
    cities: { Istanbul: 76, Ankara: 41, Izmir: 25, Bursa: 18, Antalya: 17 },
  },
  {
    brand: "Renault",
    series: "Clio",
    models: ["Tum paketler", "Joy", "Touch", "Icon", "Evolution"],
    basePrice: 745000,
    median: 785000,
    count: 860,
    cleanCount: 163,
    cities: { Istanbul: 146, Ankara: 118, Izmir: 88, Bursa: 74, Adana: 58 },
  },
  {
    brand: "Tesla",
    series: "Model Y",
    models: ["Tum paketler", "Long Range", "Performance", "Arkadan Itis"],
    basePrice: 3090000,
    median: 3160000,
    count: 96,
    cleanCount: 19,
    cities: { Istanbul: 38, Ankara: 17, Izmir: 12, Antalya: 8, Bursa: 7 },
  },
];

const formatTry = (value) =>
  `${Math.round(value).toLocaleString("tr-TR")} TL`;

const form = document.querySelector("#vehicleForm");
const brandSelect = document.querySelector("#brandSelect");
const seriesSelect = document.querySelector("#seriesSelect");
const modelSelect = document.querySelector("#modelSelect");
const yearInput = document.querySelector("#yearInput");
const mileageInput = document.querySelector("#mileageInput");
const priceInput = document.querySelector("#priceInput");
const cleanOnlyInput = document.querySelector("#cleanOnlyInput");

const priceRange = document.querySelector("#priceRange");
const marketComment = document.querySelector("#marketComment");
const confidenceTag = document.querySelector("#confidenceTag");
const sampleTag = document.querySelector("#sampleTag");
const positionTag = document.querySelector("#positionTag");
const distributionBars = document.querySelector("#distributionBars");
const cityList = document.querySelector("#cityList");
const listingRows = document.querySelector("#listingRows");
const canvas = document.querySelector("#trendCanvas");

function fillBrands() {
  brandSelect.innerHTML = marketData
    .map((item) => `<option value="${item.brand}">${item.brand}</option>`)
    .join("");
  fillSeries();
}

function currentBrandItems() {
  return marketData.filter((item) => item.brand === brandSelect.value);
}

function fillSeries() {
  seriesSelect.innerHTML = currentBrandItems()
    .map((item) => `<option value="${item.series}">${item.series}</option>`)
    .join("");
  fillModels();
}

function currentSegment() {
  return (
    marketData.find(
      (item) => item.brand === brandSelect.value && item.series === seriesSelect.value,
    ) || marketData[0]
  );
}

function fillModels() {
  const segment = currentSegment();
  modelSelect.innerHTML = segment.models
    .map((item) => `<option value="${item}">${item}</option>`)
    .join("");
  runAnalysis();
}

function estimateMarket(segment) {
  const year = Number(yearInput.value) || 2020;
  const mileage = Number(mileageInput.value) || 0;
  const userPrice = Number(priceInput.value) || 0;
  const ageFactor = Math.max(0.72, 1 - (2026 - year) * 0.035);
  const mileageFactor = Math.max(0.72, 1 - mileage / 950000);
  const modelFactor = modelSelect.value === "Tum paketler" ? 1 : 1.035;
  const cleanFactor = cleanOnlyInput.checked ? 1.045 : 1;
  const median = segment.median * ageFactor * mileageFactor * modelFactor * cleanFactor;
  const low = median * 0.93;
  const high = median * 1.08;
  const delta = userPrice ? ((userPrice - median) / median) * 100 : 0;
  const confidence = segment.count >= 200 ? "Yuksek" : segment.count >= 100 ? "Orta" : "Dusuk";
  const position = !userPrice
    ? "Fiyat girilmedi"
    : delta < -8
      ? "Piyasa alti"
      : delta > 8
        ? "Piyasa ustu"
        : "Piyasa icinde";
  return { median, low, high, delta, confidence, position };
}

function renderDistribution(median) {
  const buckets = [
    { label: "Alt bant", value: 42, price: median * 0.9 },
    { label: "Uygun bant", value: 78, price: median * 0.98 },
    { label: "Medyan", value: 100, price: median },
    { label: "Ust bant", value: 66, price: median * 1.08 },
    { label: "Yuksek", value: 31, price: median * 1.18 },
  ];
  distributionBars.innerHTML = buckets
    .map(
      (bucket) => `
        <div class="bar-row">
          <span>${bucket.label}</span>
          <div class="bar-track"><div class="bar-fill" style="width:${bucket.value}%"></div></div>
          <strong>${formatTry(bucket.price)}</strong>
        </div>
      `,
    )
    .join("");
}

function renderCities(segment) {
  const max = Math.max(...Object.values(segment.cities));
  cityList.innerHTML = Object.entries(segment.cities)
    .map(
      ([city, count]) => `
        <div class="city-row">
          <span>${city}</span>
          <div class="city-track"><div class="city-fill" style="width:${(count / max) * 100}%"></div></div>
          <strong>${count} ilan</strong>
        </div>
      `,
    )
    .join("");
}

function renderListings(segment, median) {
  const cities = Object.keys(segment.cities);
  const rows = Array.from({ length: 8 }, (_, index) => {
    const price = median * (0.9 + index * 0.035);
    const year = Number(yearInput.value) - (index % 3);
    const km = Number(mileageInput.value) + index * 7000;
    return {
      title: `${segment.brand} ${segment.series} ${modelSelect.value}`,
      year,
      km,
      city: cities[index % cities.length],
      price,
    };
  });
  listingRows.innerHTML = rows
    .map(
      (row) => `
        <tr>
          <td>${row.title}</td>
          <td>${row.year}</td>
          <td>${row.km.toLocaleString("tr-TR")} km</td>
          <td>${row.city}</td>
          <td>${formatTry(row.price)}</td>
        </tr>
      `,
    )
    .join("");
}

function renderTrend(median) {
  const ctx = canvas.getContext("2d");
  const width = canvas.clientWidth * devicePixelRatio;
  const height = canvas.height * devicePixelRatio;
  canvas.width = width;
  canvas.height = height;
  ctx.scale(devicePixelRatio, devicePixelRatio);
  ctx.clearRect(0, 0, canvas.clientWidth, canvas.height);

  const points = [0.93, 0.95, 0.98, 0.97, 1.01, 1.03, 1.0].map((factor) => median * factor);
  const min = Math.min(...points);
  const max = Math.max(...points);
  const pad = 24;
  const usableW = canvas.clientWidth - pad * 2;
  const usableH = canvas.height - pad * 2;

  ctx.strokeStyle = "#2c3a4d";
  ctx.lineWidth = 1;
  for (let i = 0; i < 4; i += 1) {
    const y = pad + (usableH / 3) * i;
    ctx.beginPath();
    ctx.moveTo(pad, y);
    ctx.lineTo(canvas.clientWidth - pad, y);
    ctx.stroke();
  }

  ctx.strokeStyle = "#6ea8fe";
  ctx.lineWidth = 3;
  ctx.beginPath();
  points.forEach((value, index) => {
    const x = pad + (usableW / (points.length - 1)) * index;
    const y = pad + usableH - ((value - min) / (max - min || 1)) * usableH;
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.fillStyle = "#48c7a7";
  points.forEach((value, index) => {
    const x = pad + (usableW / (points.length - 1)) * index;
    const y = pad + usableH - ((value - min) / (max - min || 1)) * usableH;
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();
  });
}

function runAnalysis() {
  const segment = currentSegment();
  const result = estimateMarket(segment);
  const sampleCount = cleanOnlyInput.checked ? segment.cleanCount : segment.count;

  priceRange.textContent = `${formatTry(result.low)} - ${formatTry(result.high)}`;
  marketComment.textContent = `Bu secime en yakin ilanlarda agirlikli medyan ${formatTry(result.median)}. Girilen fiyat bu medyana gore ${
    result.delta ? `%${Math.abs(result.delta).toFixed(1)} ${result.delta > 0 ? "yukarida" : "asagida"}` : "karsilastirilmayacak durumda"
  }.`;
  confidenceTag.textContent = `Guven: ${result.confidence}`;
  sampleTag.textContent = `Orneklem: ${sampleCount} ilan`;
  positionTag.textContent = `Piyasa: ${result.position}`;

  renderDistribution(result.median);
  renderCities(segment);
  renderListings(segment, result.median);
  renderTrend(result.median);
}

brandSelect.addEventListener("change", fillSeries);
seriesSelect.addEventListener("change", fillModels);
modelSelect.addEventListener("change", runAnalysis);
[yearInput, mileageInput, priceInput, cleanOnlyInput].forEach((input) =>
  input.addEventListener("input", runAnalysis),
);
form.addEventListener("submit", (event) => {
  event.preventDefault();
  runAnalysis();
  document.querySelector("#market").scrollIntoView({ behavior: "smooth", block: "start" });
});
window.addEventListener("resize", runAnalysis);

fillBrands();
