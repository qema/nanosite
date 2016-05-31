Title: Tie-Dye Algorithm

![Tie-Dye](http://wanganzhou.com/images/tie-dye/tie-dye2.png)

I have program to generate CS-infused tie-dyes with Prim's Algorithm. You can check it out on GitHub here: [Tie-Dye](https://github.com/qema/tie-dye). Create and share your tie-dye creations with the world!

## Method

The tie-dyes are generated with [Prim's Minimum Spanning Tree Algorithm](https://en.wikipedia.org/wiki/Prim%27s_algorithm), which is a really cool algorithm to connect the vertices of a graph, specifically creating a tree with shortest total edge length (or "weight"). It's used for anything from maze generation to circuit design.

Here's how the Tie Dye works.

We start out with the idea of turning our computer screen into a graph, with a vertex at every pixel.

![Graph it!](http://wanganzhou.com/images/tie-dye/graph-empty.png)

We make a full grid connecting all vertices, assigning random weight to each edge.

![Connect](http://wanganzhou.com/images/tie-dye/graph-full.png)

Next we use Prim's Algorithm to connect the edges in a tree. This gets rid of any loops in the graph. Now our computer tie dye will flow into new spaces instead of mixing with itself, just like water tension does for real tie dye.

![Prim It!](http://wanganzhou.com/images/tie-dye/graph0.png)

Now, starting from a random point, we'll do a paint bucket fill on it (specifically a [Depth First Search](https://en.wikipedia.org/wiki/Depth-first_search)). Except, ours will be a special rainbow paint bucket that changes color after each step, and can only flow along the edges.

![Flow](http://wanganzhou.com/images/tie-dye/graph1.png)

![Flow](http://wanganzhou.com/images/tie-dye/graph2.png)

![Flow](http://wanganzhou.com/images/tie-dye/graph3.png)

![Flow](http://wanganzhou.com/images/tie-dye/graph4.png)

![Flow](http://wanganzhou.com/images/tie-dye/graph5.png)

Now we have a rainbow tie-dye pattern!

![Tie-Dye](http://wanganzhou.com/images/tie-dye/tie-dye1.png)