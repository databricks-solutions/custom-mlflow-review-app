import { ItemRenderer, RendererRegistry } from "@/types/renderers";
import { DefaultItemRenderer } from "./DefaultItemRenderer";
import { ToolRenderer } from "./ToolRenderer";

class RendererRegistryImpl implements RendererRegistry {
  public renderers = new Map<string, ItemRenderer>();
  public defaultRenderer = "default";

  constructor() {
    // Register the default renderer
    this.registerRenderer({
      name: "default",
      displayName: "Default Renderer",
      description:
        "Standard MLflow trace review interface with conversation view and labeling forms",
      component: DefaultItemRenderer,
    });

    // Register the tool renderer
    this.registerRenderer({
      name: "tool-renderer",
      displayName: "Tool Renderer",
      description:
        "Conversation view with detailed tool execution details and comprehensive labeling interface",
      component: ToolRenderer,
    });
  }

  getRenderer(name?: string): ItemRenderer {
    const rendererName = name || this.defaultRenderer;
    const renderer = this.renderers.get(rendererName);

    if (!renderer) {
      console.warn(`Renderer '${rendererName}' not found, falling back to default`);
      return this.renderers.get(this.defaultRenderer)!;
    }

    return renderer;
  }

  registerRenderer(renderer: ItemRenderer): void {
    this.renderers.set(renderer.name, renderer);
  }

  listRenderers(): ItemRenderer[] {
    return Array.from(this.renderers.values());
  }
}

// Global registry instance
export const rendererRegistry = new RendererRegistryImpl();

// Helper function to get a renderer component
export function getRendererComponent(name?: string) {
  return rendererRegistry.getRenderer(name).component;
}
