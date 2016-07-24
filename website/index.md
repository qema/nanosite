    {{ #for post in newest 5 posts }}
	<article>
	  <div>{{ post.title }}</div>
	  <div>{{{ post.content }}}</div>
	</article>
	{{ #endfor }}

nanosite is the tiny huge static-site generator. 

# tiny
Minimalism is empowering. nanosite was created as a response to traditional static-site generators that force your content to conform to a format.

nanosite has a tiny footprint: it imposes no restriction on the structure of your site. So you can finally control every detail of your site's design, whether you're making a blog, organization page or portfolio.

# huge
All of the useful features are there when you need them.

- Powerful templating language
- Built-in server with debugger
- Plugins and themes
- Extensible macros
- Markdown
- RSS