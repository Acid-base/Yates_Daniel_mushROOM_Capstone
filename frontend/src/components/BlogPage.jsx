// src/components/BlogPage.jsx
import React, { useState, useEffect } from 'react';
import BlogPost from './BlogPost';
const BlogPage = () => {
  const [posts, setPosts] = useState([]);

  useEffect(() => {
    fetch('https://your-api-base-url.com/posts') // Update with your actual API URL
      .then(res => res.json())
      .then(data => setPosts(data))
      .catch(error => console.error('Error fetching posts:', error));
  }, []);

  return (
    <div>
      <h1>Blog</h1>
      {posts.map(post => (
        <BlogPost
          key={post.id}
          title={post.title}
          content={post.content}
          date={post.date}
        />
      ))}
    </div>
  );
};

export default BlogPage;
