import { SellingPartner } from 'amazon-sp-api';
import * as fs from 'fs';
import * as path from 'path';

// 1. Configure debug logging properly
const debug = require('debug')('sp-api');

// Constants with explicit type
const USE_CASE_TO_REQUIREMENTS = {
  'LISTING': 'LISTING',
  'LISTINGS_OFFER_ONLY': 'LISTINGS_OFFER_ONLY'
} as const;

type UseCase = keyof typeof USE_CASE_TO_REQUIREMENTS;

// Product data structure
interface ProductData {
  sku: string;
  productType: string;
  useCase: UseCase; // Now strictly typed
  attributes: object;
}

// SP-API Configuration
interface SpApiConfig {
  region: 'eu' | 'na' | 'fe';
  refresh_token: string;
  credentials: {
    SELLING_PARTNER_APP_CLIENT_ID: string;
    SELLING_PARTNER_APP_CLIENT_SECRET: string;
  };
  sellingPartnerId: string;
  marketplaceId: string;
}

// Load settings (No AWS keys)
const loadSettings = (): SpApiConfig => {
  return {
    region: 'na', // Change to your region
    refresh_token: 'Atzr|IwEBICFycc-9WLwEw4N7hXQScOtzWBNXohwq_lfoI8x7pLS67HChpY6EEwxjlYNJalIwFzl38wuCKw_-j0VzQLc0Cjw7d1_Dx60Nu3IPOOFwy-0TKjBN-CHtfSsVfPnD2JZ9eQoXUmzuNz8eP-eUSLtBjHxpJac3H05fNXujP2kx-XjoaYrLkOMakQ09yZss_OBYyP1HY-_4JG-b7yxy6GuORIVcnx3wns8WyrNQL3tYx71yN-iJCFasx07c7qogztTEO6EwIUV9zaxqJmwxRKiRWf05N-MEFexgDrAYuDA-GycI4tQNSHGk7yhpZuOPodlDtEV4SldGaL86nDKoBkryjX40', // From OAuth flow
    credentials: {
      SELLING_PARTNER_APP_CLIENT_ID: 'amzn1.application-oa2-client.66d2269ea5344f11990b1f0df044e540', // From Seller Central
      SELLING_PARTNER_APP_CLIENT_SECRET: 'mzn1.oa2-cs.v1.92f7c818bc2458e6e29688c3dea9968be1f6a3294fa693929c3771da16f8c1d8' // From Seller Central
    },
    sellingPartnerId: 'A1JCZW9YA2XDCG', // Found in Seller Central → Settings → Account Info
    marketplaceId: 'ATVPDKIKX0DER' // US Sandbox Marketplace ID
  };
};

// 3. Create client with proper debugging
const createSpApiClient = async (config: SpApiConfig) => {
  try {
    debug('Initializing SP-API client with config:', {
      region: config.region,
      clientId: config.credentials.SELLING_PARTNER_APP_CLIENT_ID.substring(0, 8) + '...',
      sellerId: config.sellingPartnerId
    });

    const client = new SellingPartner({
      region: config.region,
      refresh_token: config.refresh_token,
      credentials: {
        SELLING_PARTNER_APP_CLIENT_ID: config.credentials.SELLING_PARTNER_APP_CLIENT_ID,
        SELLING_PARTNER_APP_CLIENT_SECRET: config.credentials.SELLING_PARTNER_APP_CLIENT_SECRET
      },
      options: {
        auto_request_tokens: true,
        debug_log: true // This enables debug logging
      }
    });

    return client;
  } catch (error) {
    debug('Client initialization failed:', error);
    throw error;
  }
};

// Load products from JSON
const loadProductsFromJson = (filePath: string): ProductData[] => {
  try {
    const rawData = fs.readFileSync(path.resolve(__dirname, filePath), 'utf-8');
    return JSON.parse(rawData);
  } catch (error) {
    console.error('❌ Error loading products JSON:', error instanceof Error ? error.message : error);
    throw error;
  }
};

// Construct the API request
const constructListingsItemPutRequest = (
  productType: string,
  useCase: UseCase, // Now strictly typed
  attributes: object
) => {
  return {
    productType,
    requirements: USE_CASE_TO_REQUIREMENTS[useCase], // Now type-safe
    attributes
  };
};

// Main function to submit listings
const listProductsOnAmazon = async () => {
  const config = loadSettings();
  const products = loadProductsFromJson('products.json');

  try {
    const spClient = await createSpApiClient(config);

    for (const product of products) {
      console.log(`🔄 Processing SKU: ${product.sku}`);

      const requestBody = constructListingsItemPutRequest(
        product.productType,
        product.useCase,
        product.attributes
      );

      try {
        const response = await spClient.callAPI({
          operation: 'putListingsItem',
          endpoint: 'listingsItems',
          path: {
            sellerId: config.sellingPartnerId,
            sku: product.sku
          },
          query: {
            marketplaceIds: [config.marketplaceId],
            issueLocale: 'en_US',
            mode: 'VALIDATION_PREVIEW'
          },
          body: requestBody
        });

        console.log(`✅ Success: ${product.sku}`, response);
      } catch (error: unknown) {
        if (error instanceof Error) {
          const apiError = error as { response?: { data?: unknown } };
          console.error(
            `❌ Failed to list ${product.sku}:`,
            apiError.response?.data || error.message
          );
        } else {
          console.error(`❌ Failed to list ${product.sku}:`, error);
        }
      }

      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  } catch (error) {
    console.error('❌ Fatal error:', error instanceof Error ? error.message : error);
  }
};

// 5. Run with debug output
require('debug').enable('sp-api');
listProductsOnAmazon().catch(err => debug('Fatal error:', err));