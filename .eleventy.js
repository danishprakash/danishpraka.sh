const syntaxHighlight = require('@11ty/eleventy-plugin-syntaxhighlight'),
  markdownLazyLoadImages = require('markdown-it-image-lazy-loading'),
  markdownIt = require('markdown-it'),
  pluginRss = require('@11ty/eleventy-plugin-rss'),
  markdownAttrs = require('markdown-it-attrs'),
  embedTwitter = require('eleventy-plugin-embed-twitter');
module.exports = function (eleventyConfig) {
  eleventyConfig.addPlugin(syntaxHighlight);
  eleventyConfig.addPlugin(pluginRss);
  eleventyConfig.addPlugin(embedTwitter);
  eleventyConfig.addPassthroughCopy('assets');

  const options = {
      html: true,
      breaks: true,
      linkify: false,
      typographer: true
    },
    markdownEngine = markdownIt(options);

  markdownEngine.use(markdownLazyLoadImages);
  markdownEngine.use(markdownAttrs);

  eleventyConfig.setLibrary('md', markdownEngine);

  return {};
};
