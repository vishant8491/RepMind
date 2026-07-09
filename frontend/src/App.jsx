import Header from './components/Header';
import LogInteractionForm from './components/LogInteractionForm';
import ChatPanel from './components/ChatPanel';
import InteractionHistory from './components/InteractionHistory';

export default function App() {
  return (
    <div className="app-shell">
      <Header />
      <div className="main-layout">
        <LogInteractionForm />
        <ChatPanel />
        <InteractionHistory />
      </div>
    </div>
  );
}
