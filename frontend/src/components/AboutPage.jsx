import React, { useState } from 'react';

function AboutPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async event => {
    event.preventDefault();

    // Send the form data to your backend endpoint
    try {
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, email, message }),
      });

      if (response.ok) {
        setSubmitted(true); // Form submitted successfully
      } else {
        console.error('Error submitting form:', response.status);
        // Handle the error (e.g., display an error message)
      }
    } catch (error) {
      console.error('Error submitting form:', error);
      // Handle network errors (e.g., display an error message)
    }
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
          <button type="submit">Submit</button>
        </form>
      )}
    </div>
  );
}

export default AboutPage;
