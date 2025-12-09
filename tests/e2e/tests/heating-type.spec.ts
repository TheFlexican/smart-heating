import { test, expect } from '@playwright/test';
import { login, navigateToSmartHeating } from './helpers';

test.describe('Heating Type Configuration Tests', () => {

  test.beforeEach(async ({ page }) => {
    await login(page);
    await navigateToSmartHeating(page);
  });

  test('should be able to set heating type via API', async ({ page, request }) => {
    // Set Woonkamer to floor heating
    const response = await request.post('http://localhost:8123/api/smart_heating/areas/woonkamer/heating_type', {
      headers: {
        'Content-Type': 'application/json',
      },
      data: {
        heating_type: 'floor_heating',
        custom_overhead_temp: 8.0,
      },
    });

    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.success).toBe(true);

    // Verify the setting persisted
    const areasResponse = await request.get('http://localhost:8123/api/smart_heating/areas');
    expect(areasResponse.status()).toBe(200);
    const areasData = await areasResponse.json();

    const woonkamer = areasData.areas.find((a: any) => a.id === 'woonkamer');
    expect(woonkamer).toBeDefined();
    expect(woonkamer.heating_type).toBe('floor_heating');
    expect(woonkamer.custom_overhead_temp).toBe(8.0);
  });

  test('should validate heating type values', async ({ request }) => {
    // Try to set invalid heating type
    const invalidResponse = await request.post('http://localhost:8123/api/smart_heating/areas/woonkamer/heating_type', {
      headers: {
        'Content-Type': 'application/json',
      },
      data: {
        heating_type: 'invalid_type',
      },
    });

    expect(invalidResponse.status()).toBe(400);
    const errorData = await invalidResponse.json();
    expect(errorData.error).toBeDefined();
  });

  test('should validate custom overhead temperature range', async ({ request }) => {
    // Try to set overhead temp too high
    const tooHighResponse = await request.post('http://localhost:8123/api/smart_heating/areas/woonkamer/heating_type', {
      headers: {
        'Content-Type': 'application/json',
      },
      data: {
        custom_overhead_temp: 50.0,
      },
    });

    expect(tooHighResponse.status()).toBe(400);
    const errorData = await tooHighResponse.json();
    expect(errorData.error).toContain('30');

    // Try to set negative overhead temp
    const negativeResponse = await request.post('http://localhost:8123/api/smart_heating/areas/woonkamer/heating_type', {
      headers: {
        'Content-Type': 'application/json',
      },
      data: {
        custom_overhead_temp: -5.0,
      },
    });

    expect(negativeResponse.status()).toBe(400);
  });

  test('should allow setting radiator type', async ({ request }) => {
    const response = await request.post('http://localhost:8123/api/smart_heating/areas/keuken/heating_type', {
      headers: {
        'Content-Type': 'application/json',
      },
      data: {
        heating_type: 'radiator',
      },
    });

    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.success).toBe(true);

    // Verify it persisted
    const areasResponse = await request.get('http://localhost:8123/api/smart_heating/areas');
    const areasData = await areasResponse.json();

    const keuken = areasData.areas.find((a: any) => a.id === 'keuken');
    expect(keuken.heating_type).toBe('radiator');
  });

  test('should allow clearing custom overhead temperature', async ({ request }) => {
    // First set a custom overhead
    await request.post('http://localhost:8123/api/smart_heating/areas/woonkamer/heating_type', {
      headers: {
        'Content-Type': 'application/json',
      },
      data: {
        custom_overhead_temp: 10.0,
      },
    });

    // Then clear it
    const response = await request.post('http://localhost:8123/api/smart_heating/areas/woonkamer/heating_type', {
      headers: {
        'Content-Type': 'application/json',
      },
      data: {
        custom_overhead_temp: null,
      },
    });

    expect(response.status()).toBe(200);

    // Verify it was cleared
    const areasResponse = await request.get('http://localhost:8123/api/smart_heating/areas');
    const areasData = await areasResponse.json();

    const woonkamer = areasData.areas.find((a: any) => a.id === 'woonkamer');
    expect(woonkamer.custom_overhead_temp).toBeNull();
  });

  test('should return 404 for non-existent area', async ({ request }) => {
    const response = await request.post('http://localhost:8123/api/smart_heating/areas/nonexistent/heating_type', {
      headers: {
        'Content-Type': 'application/json',
      },
      data: {
        heating_type: 'floor_heating',
      },
    });

    expect(response.status()).toBe(404);
    const errorData = await response.json();
    expect(errorData.error).toContain('not found');
  });
});
