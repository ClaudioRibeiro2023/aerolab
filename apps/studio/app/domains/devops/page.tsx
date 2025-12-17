"use client";

import { useState } from "react";
import { GitBranch, GitPullRequest, AlertCircle, CheckCircle2, ExternalLink } from "lucide-react";
import { PageHeader } from "../../../components/PageHeader";
import { PageSection } from "../../../components/PageSection";
import { Badge } from "../../../components/Badge";

export default function DevOpsDashboard() {
  const [repos] = useState([
    { name: 'agno-template', private: true, stars: 12, issues: 3, prs: 2 },
    { name: 'my-app', private: false, stars: 45, issues: 8, prs: 5 },
    { name: 'api-server', private: true, stars: 0, issues: 1, prs: 0 },
  ]);

  const [deploys] = useState([
    { site: "my-app.netlify.app", status: "ready", branch: "main", time: "2 min ago" },
    { site: "api-docs.netlify.app", status: "building", branch: "docs", time: "1 min ago" },
    { site: "staging.netlify.app", status: "failed", branch: "develop", time: "5 min ago" },
  ]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="DevOps"
        subtitle="GitHub, Netlify, Supabase"
        leadingAction={
          <div className="bg-purple-500 p-3 rounded-xl text-white shadow-lg">
            <GitBranch className="w-6 h-6" />
          </div>
        }
        breadcrumbs={[
          { label: "Domínios", href: "/domains" },
          { label: "DevOps" },
        ]}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PageSection title="Repositórios GitHub">
          <div className="space-y-3">
            {repos.map((repo) => (
              <div key={repo.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className={`w-2 h-2 rounded-full ${repo.private ? "bg-yellow-500" : "bg-green-500"}`} />
                  <span className="font-medium">{repo.name}</span>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <span className="flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    {repo.issues}
                  </span>
                  <span className="flex items-center gap-1">
                    <GitPullRequest className="w-4 h-4" />
                    {repo.prs}
                  </span>
                  <button className="text-purple-500 hover:text-purple-700" title="Abrir repositório" aria-label="Abrir repositório">
                    <ExternalLink className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </PageSection>

        <PageSection title="Deploys Netlify">
          <div className="space-y-3">
            {deploys.map((deploy) => (
              <div key={deploy.site} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium">{deploy.site}</p>
                  <p className="text-sm text-gray-500">{deploy.branch} • {deploy.time}</p>
                </div>
                <div className="flex items-center gap-2">
                  {deploy.status === "ready" && (
                    <Badge variant="success" className="flex items-center gap-1 text-xs">
                      <CheckCircle2 className="w-4 h-4" />
                      Pronto
                    </Badge>
                  )}
                  {deploy.status === "building" && (
                    <Badge variant="warning" className="flex items-center gap-1 text-xs">
                      <div className="w-3 h-3 border-2 border-yellow-500 border-t-transparent rounded-full animate-spin" />
                      Building
                    </Badge>
                  )}
                  {deploy.status === "failed" && (
                    <Badge variant="error" className="flex items-center gap-1 text-xs">
                      <AlertCircle className="w-4 h-4" />
                      Falhou
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </PageSection>
      </div>
    </div>
  );
}
