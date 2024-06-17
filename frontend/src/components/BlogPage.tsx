import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchBlogPosts } from '../api';
import BlogPost from './BlogPost';

interface BlogPostProps {
  id: number;
  title: string;
  content: string;
  date: string;
}

const BlogPage: React.FC = () => {
  const { isLoading, error, data: posts } = useQuery('blogPosts', fetchBlogPosts);

  if (isLoading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div>
      <h1>Blog</h1>
      {posts.map((post: BlogPostProps) => (
        <BlogPost key={post.id} title={post.title} content={post.content} date={post.date} />
      ))}
    </div>
  );
};

export default BlogPage;
