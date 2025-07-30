import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';

test('renders AI Video Editor', () => {
  render(<App />);
  const headerElement = screen.getByText(/AI Video Editor/i);
  expect(headerElement).toBeInTheDocument();
});