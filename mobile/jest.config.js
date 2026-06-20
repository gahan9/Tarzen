// SPDX-License-Identifier: MIT
/**
 * Jest configuration for the mobile app's pure-logic unit tests.
 *
 * The offline log queue, reconnect-sync manager, and consent gate are written
 * as dependency-injected, framework-free modules so they can be tested in a
 * plain Node environment without booting React Native or mocking heavy native
 * modules. Native adapters (AsyncStorage, NetInfo, expo-*) are imported only by
 * thin wiring files that these tests never load.
 */
module.exports = {
  preset: "ts-jest",
  testEnvironment: "node",
  roots: ["<rootDir>/src", "<rootDir>/__tests__"],
  testMatch: ["**/__tests__/**/*.test.ts"],
  moduleNameMapper: {
    "^@carbon/shared-types$": "<rootDir>/../packages/shared-types/src/index.ts",
  },
  transform: {
    "^.+\\.tsx?$": ["ts-jest", { tsconfig: "<rootDir>/tsconfig.jest.json" }],
  },
  clearMocks: true,
};
