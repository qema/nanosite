Title: Author

![Author](http://wanganzhou.com/images/author/screenshot.png)

Author is an exploration in simple text classification. It figures out an author's unique "word signature", which is the distribution of word frequencies in their writing. Based on this, it can take any piece of writing and figure out who wrote it!

You can check it out on GitHub: [Author](https://github.com/qema/author).

Makes use of cool probability tools like [Bayes' Theorem](http://betterexplained.com/articles/an-intuitive-and-short-explanation-of-bayes-theorem/)!

How it works: we want to find out "What is the probability that author A wrote book X, if we know that X has a certain word composition?" It turns out that we can use Bayes' Theorem to flip this around, into "What is the probability that X has a certain word composition, if we know that author A wrote the book?" Well, since we know the authors' "word signatures", we already know how to do that -- all we have to do is tally up words! It seems like Bayes' Theorem has the power to reverse causation! What will you do with your new superpower?