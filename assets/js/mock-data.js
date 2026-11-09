/* 공통 계약 파일: 구조·ID 변경 전 팀원과 협의. 모든 이름·수치는 가상 예시. */
window.CafeMock = {
  brands: [
    { id: "starbucks", name: "스타벅스", initial: "S", color: "#476953" },
    { id: "compose", name: "컴포즈커피", initial: "C", color: "#96722b" },
    { id: "paik", name: "빽다방", initial: "P", color: "#9a5550" },
    { id: "mega", name: "메가커피", initial: "M", color: "#a48028" }
  ],
  categories: [
    { id: "caffeine", name: "카페인" }, { id: "decaf", name: "디카페인" },
    { id: "yogurt", name: "요거트" }, { id: "icecream", name: "아이스크림&빙수" },
    { id: "latte", name: "라떼" }, { id: "smoothie", name: "프라페&스무디" },
    { id: "fruit", name: "과일" }
  ],
  stores: [
    { id: "demo-store-s", brandId: "starbucks", name: "스타벅스 예시 매장", description: "숭실대 주변 · 가상 매장 A", x: 40, y: 32 },
    { id: "demo-store-c", brandId: "compose", name: "컴포즈커피 예시 매장", description: "숭실대 주변 · 가상 매장 B", x: 23, y: 63 },
    { id: "demo-store-p", brandId: "paik", name: "빽다방 예시 매장", description: "숭실대 주변 · 가상 매장 C", x: 73, y: 43 },
    { id: "demo-store-m", brandId: "mega", name: "메가커피 예시 매장", description: "숭실대 주변 · 가상 매장 D", x: 62, y: 76 }
  ],
  menus: [
    { id: "demo-s-latte", brandId: "starbucks", name: "예시 아이스 라떼", categoryTags: ["caffeine", "latte"], sizeLabel: "최소 사이즈(예시)", volumeMl: 350, temperature: "ICE", priceKrw: 5000, sugarG: 8, caloriesKcal: 120, tone: "latte", isNew: false, seasonal: false },
    { id: "demo-s-matcha", brandId: "starbucks", name: "예시 말차 크림 라떼", categoryTags: ["caffeine", "latte"], sizeLabel: "최소 사이즈(예시)", volumeMl: 350, temperature: "ICE", priceKrw: 6000, sugarG: 25, caloriesKcal: 240, tone: "matcha", isNew: true, seasonal: true },
    { id: "demo-s-decaf", brandId: "starbucks", name: "예시 디카페인 커피", categoryTags: ["decaf"], sizeLabel: "최소 사이즈(예시)", volumeMl: 350, temperature: "HOT", priceKrw: 4800, sugarG: 0, caloriesKcal: 10, tone: "coffee", isNew: false, seasonal: false },
    { id: "demo-c-latte", brandId: "compose", name: "예시 바닐라 라떼", categoryTags: ["caffeine", "latte"], sizeLabel: "최소 사이즈(예시)", volumeMl: 450, temperature: "ICE", priceKrw: 3800, sugarG: 22, caloriesKcal: 210, tone: "latte", isNew: false, seasonal: false },
    { id: "demo-c-yogurt", brandId: "compose", name: "예시 딸기 요거트", categoryTags: ["yogurt", "smoothie", "fruit"], sizeLabel: "최소 사이즈(예시)", volumeMl: 450, temperature: "ICE", priceKrw: 4500, sugarG: 36, caloriesKcal: 290, tone: "berry", isNew: true, seasonal: true },
    { id: "demo-c-coffee", brandId: "compose", name: "예시 아메리카노", categoryTags: ["caffeine"], sizeLabel: "최소 사이즈(예시)", volumeMl: 450, temperature: "ICE", priceKrw: 2000, sugarG: 0, caloriesKcal: 15, tone: "coffee", isNew: false, seasonal: false },
    { id: "demo-h-milk", brandId: "paik", name: "예시 크림 밀크티", categoryTags: ["caffeine", "latte"], sizeLabel: "최소 사이즈(예시)", volumeMl: 350, temperature: "HOT", priceKrw: 5500, sugarG: 27, caloriesKcal: 230, tone: "tea", isNew: true, seasonal: false },
    { id: "demo-h-lemon", brandId: "paik", name: "예시 레몬 티", categoryTags: ["fruit"], sizeLabel: "최소 사이즈(예시)", volumeMl: 350, temperature: "ICE", priceKrw: 5000, sugarG: 20, caloriesKcal: 100, tone: "lemon", isNew: false, seasonal: false },
    { id: "demo-h-icecream", brandId: "paik", name: "예시 커피 아이스크림", categoryTags: ["caffeine", "icecream"], sizeLabel: "최소 사이즈(예시)", volumeMl: null, temperature: "ICE", priceKrw: 6000, sugarG: 30, caloriesKcal: 320, tone: "latte", isNew: false, seasonal: false },
    { id: "demo-m-matcha", brandId: "mega", name: "예시 말차 라떼", categoryTags: ["caffeine", "latte"], sizeLabel: "최소 사이즈(예시)", volumeMl: 450, temperature: "ICE", priceKrw: 4000, sugarG: 28, caloriesKcal: 250, tone: "matcha", isNew: false, seasonal: false },
    { id: "demo-m-berry", brandId: "mega", name: "예시 베리 스무디", categoryTags: ["smoothie", "fruit"], sizeLabel: "최소 사이즈(예시)", volumeMl: 450, temperature: "ICE", priceKrw: 4500, sugarG: 40, caloriesKcal: 280, tone: "berry", isNew: true, seasonal: true },
    { id: "demo-m-decaf", brandId: "mega", name: "예시 디카페인 라떼", categoryTags: ["decaf", "latte"], sizeLabel: "최소 사이즈(예시)", volumeMl: 450, temperature: "HOT", priceKrw: null, sugarG: null, caloriesKcal: null, tone: "latte", isNew: false, seasonal: false }
  ].map(function (menu) { return Object.assign(menu, { sourceUrl: null, checkedAt: null, isDemo: true }); }),
  trends: [
    { id: "demo-trend-matcha", title: "쌉싸름한 말차의 매력", keyword: "말차", description: "말차가 들어간 메뉴를 브랜드별로 둘러보세요.", label: "키워드 예시", tone: "matcha", sourceUrl: null, period: null },
    { id: "demo-trend-milk", title: "부드러운 우유 한 잔", keyword: "라떼", description: "같은 라떼도 가격과 당류는 다를 수 있어요.", label: "키워드 예시", tone: "latte", sourceUrl: null, period: null },
    { id: "demo-trend-berry", title: "과일로 더하는 산뜻함", keyword: "베리", description: "과일이 들어간 음료의 정보를 함께 살펴보세요.", label: "키워드 예시", tone: "berry", sourceUrl: null, period: null }
  ]
};