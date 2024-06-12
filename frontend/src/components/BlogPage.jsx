// src/components/BlogPage.jsx
import React, { useState, useEffect } from 'react';
import BlogPost from './BlogPost'; 
function BlogPage() {
  const blogPosts = [
    // ... array of blog post data objects
  ];

  return (
    <div>
      <h1>Mushroom News & Insights</h1>
      <ul>
        {blogPosts.map((post) => (
          <li key={post.id}>
            <BlogPost post={post} /> 
          </li>
        ))}
      </ul>
    </div>
  );
}

// Export the BlogPage component as the default export
export default BlogPage; 