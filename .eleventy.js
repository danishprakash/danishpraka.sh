module.exports = function (eleventyConfig) {
  // Aliases are in relation to the _includes folder
  eleventyConfig.addLayoutAlias('about', 'layouts/about.html');
  eleventyConfig.addLayoutAlias('books', 'layouts/books.html');
  eleventyConfig.addLayoutAlias('default', 'layouts/default.html');
  eleventyConfig.addLayoutAlias('post', 'layouts/default.html');

  return {
    dir: {
      input: './',
      output: './_site'
    }
  };
};
