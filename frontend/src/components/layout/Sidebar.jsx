import React from "react";
import { Link } from "react-router-dom";
import { cn } from "../../lib/utils";
import {
  Home,
  MessageSquare,
  Upload,
  FileText,
  Sparkles
} from "lucide-react";

const navItems = [
  { icon: Home, label: "Home", href: "/" },
  { icon: MessageSquare, label: "Chat", href: "/chat" },
  { icon: Upload, label: "Upload", href: "/upload" },
  { icon: FileText, label: "Reports", href: "/reports" },
];

const NavItem = ({ icon: Icon, label, href, active }) => {
  return (
    <Link
      to={href}
      className={cn(
        "flex flex-col items-center gap-1 px-2 my-2 py-1 w-full rounded-xl text-xs font-medium transition-colors",
        active
          ? "bg-primary/20"
          : "text-gray-700 hover:text-gray-900 hover:bg-primary/10"
      )}
    >
      <Icon className="h-5 w-5" />
      <span>{label}</span>
    </Link>
  );
};

export function Sidebar({ className }) {
  const pathname = window.location.pathname;

  return (
    <div className={cn("flex h-full w-[72px] flex-col", className)}>
      <div className="flex h-14 items-center justify-center border-b">
        <div className="flex items-center justify-center rounded-md p-1.5">
          <Sparkles className="h-6 w-6 text-blue-900" />
        </div>
      </div>
      <nav className="flex flex-col items-center gap-2 px-1 py-4">
        {navItems.map((item, index) => (
          <NavItem
            key={index}
            icon={item.icon}
            label={item.label}
            href={item.href}
            active={pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))}
          />
        ))}
      </nav>
    </div>
  );
} 