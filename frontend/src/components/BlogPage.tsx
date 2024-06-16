// frontend/src/components/BlogPage.tsx
import React from "react";
import { useQuery } from "@tanstack/react-query";
import BlogPost from "./BlogPost";

interface BlogPostProps {
  id: number;
  title: string;
  content: string;
  date: string;
}

const BlogPage = () => {
  const {
    isLoading,
    error,
    data: posts,
  } = useQuery<BlogPostProps[], Error>("posts", async () => {
    const res = await fetch("https://your-api-base-url.com/posts"); // Update with your actual API URL
    return res.json();
  });

  if (isLoading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div>
      <h1>Blog</h1>
      {posts.map((post) => (
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
