// BlogPost.tsx
import React from "react";
import PropTypes from "prop-types";

interface BlogPostProps {
  title: string;
  content: string;
  date: string;
}

const BlogPost = ({ title, content, date }: BlogPostProps) => {
  return (
    <article className="blog-post">
      <h2>{title}</h2>
      <p className="post-date">{date}</p>
      <p>{content}</p>
    </article>
  );
};

BlogPost.propTypes = {
  title: PropTypes.string.isRequired,
  content: PropTypes.string.isRequired,
  date: PropTypes.string.isRequired,
};

export default BlogPost;
