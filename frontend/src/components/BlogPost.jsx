// src/components/BlogPost.jsx
import React from 'react';

function BlogPost({ post }) {
  return (
    <div>
      <h2>{post.title}</h2>
      <p>By: {post.author}</p>
      <p>Date: {new Date(post.date).toLocaleDateString()}</p>
      {post.imageUrl && <img src={post.imageUrl} alt={post.title} />}
      <p>{post.content}</p>
    </div>
  );
}

export default BlogPost;
