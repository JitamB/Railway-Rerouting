// Expo Babel config. expo-router is enabled via the preset in SDK 50+.
module.exports = function (api) {
  api.cache(true);
  return {
    presets: ["babel-preset-expo"],
  };
};
