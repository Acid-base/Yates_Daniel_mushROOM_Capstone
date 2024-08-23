// src/components/BlogPage.jsx
import React, { useState, useEffect } from 'react';
import BlogPost from './BlogPost'; // Import BlogPost from its own file
const BlogPage = () => {
  const [posts, setPosts] = useState([]);

  useEffect(() => {
    // Fetch blog posts from an API or data source
    fetch('https://api.example.com/posts')
      .then(res => res.json())
      .then(data => setPosts(data));
  }, []);

  return (
    <div>
      <h1>Blog</h1>
      {posts.map(post => (
        <BlogPost
          key={post.id}
          title={post.title}
          content={post.content}
          date={post.date} // Assuming you have a 'date' field in your data
        />
      ))}
    </div>
  );
};

export default BlogPage;
