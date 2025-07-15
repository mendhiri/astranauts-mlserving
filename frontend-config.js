/**
 * Astranauts API Configuration for Frontend Integration
 * 
 * This configuration file provides the base URLs and endpoints
 * for integrating with the Astranauts API from Next.js frontend.
 */

export const API_CONFIG = {
  // Base URLs for different environments
  BASE_URL: {
    development:
      process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8080",
    production:
      process.env.NEXT_PUBLIC_API_BASE_URL || "https://astranauts-api-xxxxxxx.run.app",
    staging:
      process.env.NEXT_PUBLIC_API_STAGING_URL || "https://staging-astranauts-api-xxxxxxx.run.app",
  },

  // Module-specific URLs
  MODULE_URLS: {
    PRABU:
      process.env.NEXT_PUBLIC_PRABU_API_URL ||
      "https://astranauts-api-xxxxxxx.run.app/api/v1/prabu",
    SARANA:
      process.env.NEXT_PUBLIC_SARANA_API_URL ||
      "https://astranauts-api-xxxxxxx.run.app/api/v1/sarana",
    SETIA:
      process.env.NEXT_PUBLIC_SETIA_API_URL ||
      "https://astranauts-api-xxxxxxx.run.app/api/v1/setia",
  },

  // API Endpoints
  ENDPOINTS: {
    // Global Health Checks
    GLOBAL: {
      HEALTH_CHECK: "/health",
      API_V1_HEALTH: "/api/v1/health",
      DOCS: "/docs",
      REDOC: "/redoc",
    },

    // PRABU Module (Credit Scoring)
    PRABU: {
      HEALTH_CHECK: "/health",
      CALCULATE_SCORE: "/calculate",
      ALTMAN_Z_SCORE: "/altman-z", 
      M_SCORE: "/m-score",
      FINANCIAL_METRICS: "/metrics",
    },

    // SARANA Module (OCR & NLP)
    SARANA: {
      HEALTH_CHECK: "/health",
      DOCUMENT_PARSE: "/document/parse",
      OCR_UPLOAD: "/ocr/upload",
      EXTRACT_DATA: "/extract",
    },

    // SETIA Module (Sentiment Analysis)
    SETIA: {
      HEALTH_CHECK: "/health",
      SENTIMENT_ANALYSIS: "/sentiment",
      NEWS_MONITORING: "/news",
      EXTERNAL_RISK: "/external-risk",
    },
  },

  // Request configurations
  DEFAULT_HEADERS: {
    "Content-Type": "application/json",
    "Accept": "application/json",
  },

  // Timeout configurations (in milliseconds)
  TIMEOUTS: {
    DEFAULT: 30000,  // 30 seconds
    UPLOAD: 120000,  // 2 minutes for file uploads
    ANALYSIS: 180000, // 3 minutes for complex analysis
  },
};

/**
 * Helper function to get the appropriate base URL based on environment
 */
export const getBaseUrl = () => {
  const env = process.env.NODE_ENV || 'development';
  return API_CONFIG.BASE_URL[env] || API_CONFIG.BASE_URL.development;
};

/**
 * Helper function to construct full API URLs
 */
export const buildApiUrl = (module, endpoint) => {
  const baseUrl = getBaseUrl();
  const modulePrefix = `/api/v1/${module.toLowerCase()}`;
  return `${baseUrl}${modulePrefix}${endpoint}`;
};

/**
 * Predefined API client configurations
 */
export const API_CLIENTS = {
  prabu: {
    baseURL: `${getBaseUrl()}/api/v1/prabu`,
    timeout: API_CONFIG.TIMEOUTS.ANALYSIS,
    headers: API_CONFIG.DEFAULT_HEADERS,
  },
  sarana: {
    baseURL: `${getBaseUrl()}/api/v1/sarana`,
    timeout: API_CONFIG.TIMEOUTS.UPLOAD,
    headers: {
      // Note: For file uploads, don't set Content-Type
      // Let the browser set it with boundary for multipart/form-data
      "Accept": "application/json",
    },
  },
  setia: {
    baseURL: `${getBaseUrl()}/api/v1/setia`,
    timeout: API_CONFIG.TIMEOUTS.ANALYSIS,
    headers: API_CONFIG.DEFAULT_HEADERS,
  },
};

/**
 * Example usage functions for each module
 */
export const API_EXAMPLES = {
  // PRABU - Credit Scoring
  prabu: {
    calculateScore: (financialData) => ({
      url: buildApiUrl('prabu', API_CONFIG.ENDPOINTS.PRABU.CALCULATE_SCORE),
      method: 'POST',
      body: JSON.stringify(financialData),
      headers: API_CONFIG.DEFAULT_HEADERS,
    }),
    
    altmanZScore: (financialData) => ({
      url: buildApiUrl('prabu', API_CONFIG.ENDPOINTS.PRABU.ALTMAN_Z_SCORE),
      method: 'POST',
      body: JSON.stringify(financialData),
      headers: API_CONFIG.DEFAULT_HEADERS,
    }),
  },

  // SARANA - OCR & NLP
  sarana: {
    parseDocument: (file, options = {}) => {
      const formData = new FormData();
      formData.append('file', file);
      Object.entries(options).forEach(([key, value]) => {
        formData.append(key, value);
      });
      
      return {
        url: buildApiUrl('sarana', API_CONFIG.ENDPOINTS.SARANA.DOCUMENT_PARSE),
        method: 'POST',
        body: formData,
        // Don't set Content-Type header for FormData
      };
    },

    ocrUpload: (file, ocrEngine = 'tesseract') => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('ocr_engine', ocrEngine);
      
      return {
        url: buildApiUrl('sarana', API_CONFIG.ENDPOINTS.SARANA.OCR_UPLOAD),
        method: 'POST',
        body: formData,
      };
    },
  },

  // SETIA - Sentiment Analysis
  setia: {
    sentimentAnalysis: (companyData) => ({
      url: buildApiUrl('setia', API_CONFIG.ENDPOINTS.SETIA.SENTIMENT_ANALYSIS),
      method: 'POST',
      body: JSON.stringify(companyData),
      headers: API_CONFIG.DEFAULT_HEADERS,
    }),

    newsMonitoring: (companyData) => ({
      url: buildApiUrl('setia', API_CONFIG.ENDPOINTS.SETIA.NEWS_MONITORING),
      method: 'POST',
      body: JSON.stringify(companyData),
      headers: API_CONFIG.DEFAULT_HEADERS,
    }),
  },
};

export default API_CONFIG;
