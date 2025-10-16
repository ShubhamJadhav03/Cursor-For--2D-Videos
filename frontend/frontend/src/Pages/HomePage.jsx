// src/pages/HomePage.jsx
import Spline from '@splinetool/react-spline';
import { Link } from 'react-router-dom'; // Used for navigation

export default function HomePage() {
  const buttonStyle = {
    position: 'absolute',
    top: '20px',
    right: '20px',
    padding: '10px 20px',
    background: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    fontSize: '16px',
    textDecoration: 'none'
  };

  return (
    <div>
      <Spline scene="https://prod.spline.design/zGXGE4P8mEz5Yufy/scene.splinecode" />
      <Link to="/editor" style={buttonStyle}>
        Go to Editor
      </Link>
    </div>
  );
}