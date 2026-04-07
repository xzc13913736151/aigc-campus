import nextVitals from "eslint-config-next/core-web-vitals";


const config = [
  ...nextVitals,
  {
    ignores: ["tests/e2e/**"],
  },
];


export default config;
