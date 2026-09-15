import { AppProviders } from "./providers";
import { AppRoutes } from "./routes";
import WebThreads from "../shared/ui/web-threads";

export function App() {
  return (
    <AppProviders>
      <div className="app-background" aria-hidden="true">
        <WebThreads
          color1="#0063ff"
          color2="#7886b4"
          color3="#FFFFFF"
          lightMode
          backgroundColor="#f8faff"
          grain={false}
          mouseInteraction
        />
      </div>
      <AppRoutes />
    </AppProviders>
  );
}
