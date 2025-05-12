import * as React from "react";
import { cn } from "../../lib/utils";

const TabsContext = React.createContext({
  selectedTab: "",
  setSelectedTab: () => { },
});

const Tabs = ({ value, onValueChange, children, className, ...props }) => {
  const [selectedTab, setSelectedTab] = React.useState(value);

  React.useEffect(() => {
    if (value !== undefined) {
      setSelectedTab(value);
    }
  }, [value]);

  const handleTabChange = (newValue) => {
    setSelectedTab(newValue);
    if (onValueChange) {
      onValueChange(newValue);
    }
  };

  return (
    <TabsContext.Provider value={{ selectedTab, setSelectedTab: handleTabChange }}>
      <div className={cn("w-full", className)} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  );
};

const TabsList = React.forwardRef(({ className, children, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground",
      className
    )}
    {...props}
  >
    {children}
  </div>
));
TabsList.displayName = "TabsList";

const TabsTrigger = React.forwardRef(({ className, value, children, ...props }, ref) => {
  const { selectedTab, setSelectedTab } = React.useContext(TabsContext);
  const isActive = selectedTab === value;

  return (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50",
        isActive
          ? "bg-background text-foreground shadow-sm"
          : "text-muted-foreground hover:bg-muted/50",
        className
      )}
      onClick={() => setSelectedTab(value)}
      data-state={isActive ? "active" : "inactive"}
      {...props}
    >
      {children}
    </button>
  );
});
TabsTrigger.displayName = "TabsTrigger";

const TabsContent = React.forwardRef(({ className, value, children, ...props }, ref) => {
  const { selectedTab } = React.useContext(TabsContext);
  const isActive = selectedTab === value;

  if (!isActive) return null;

  return (
    <div
      ref={ref}
      className={cn("mt-2", className)}
      data-state={isActive ? "active" : "inactive"}
      {...props}
    >
      {children}
    </div>
  );
});
TabsContent.displayName = "TabsContent";

export { Tabs, TabsList, TabsTrigger, TabsContent }; 