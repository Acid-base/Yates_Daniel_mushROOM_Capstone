// AboutPage.tsx (Refactored with useMutation)
import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';

interface ContactFormValues {
  name: string;
  email: string;
  message: string;
}

function AboutPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);

  const contactMutation = useMutation(
    async (data: ContactFormValues) => {
      const response = await axios.post('/api/contact', data);
      return response.data;
    },
    {
      onSuccess: () => {
        setSubmitted(true);
      },
      onError: (error: any) => {
        console.error('Error submitting form:', error);
        setSubmissionError(
          error.message || 'An error occurred during submission.'
        );
      },
    }
  );

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmissionError(null); // Clear any previous errors
    contactMutation.mutate({ name, email, message });
  };

  return (
    <div>
      <h1>About Mushroom Explorer</h1>
      {/* ... about content */}
      <h2>Contact Us</h2>
      {submitted ? (
        <p>Thank you for your message! We will get back to you soon.</p>
      ) : (
        <form onSubmit={handleSubmit}>
          <div>
            <label htmlFor="name">Name:</label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={e => setName(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="email">Email:</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="message">Message:</label>
            <textarea
              id="message"
              value={message}
              onChange={e => setMessage(e.target.value)}
            />
          </div>
          {submissionError && (
            <div className="error-message">{submissionError}</div>
          )}
          <button type="submit" disabled={contactMutation.isLoading}>
            {contactMutation.isLoading ? 'Submitting...' : 'Submit'}
          </button>
        </form>
      )}
    </div>
  );
}

export default AboutPage;
