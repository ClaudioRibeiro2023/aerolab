"use client";
import React, { useState } from "react";

interface FeedbackWidgetProps {
  executionId: string;
  agentName: string;
  onSubmit: (feedback: {
    executionId: string;
    rating: number;
    wasHelpful: boolean;
    issues?: string[];
    suggestions?: string;
  }) => void;
}

const feedbackIssues = [
  { id: "incorrect", label: "Resposta incorreta", icon: "❌" },
  { id: "slow", label: "Muito lento", icon: "🐌" },
  { id: "incomplete", label: "Resposta incompleta", icon: "📝" },
  { id: "formatting", label: "Formatação ruim", icon: "🎨" },
  { id: "tone", label: "Tom inadequado", icon: "🗣️" },
  { id: "other", label: "Outro problema", icon: "⚠️" },
];

export default function FeedbackWidget({ executionId, agentName, onSubmit }: FeedbackWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [rating, setRating] = useState<number | null>(null);
  const [selectedIssues, setSelectedIssues] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleRatingClick = (value: number) => {
    setRating(value);
    if (value >= 4) {
      // Alta satisfação - enviar direto
      handleSubmit(value, true, [], "");
    } else {
      // Baixa satisfação - pedir detalhes
      setIsOpen(true);
    }
  };

  const toggleIssue = (issueId: string) => {
    setSelectedIssues(prev =>
      prev.includes(issueId)
        ? prev.filter(id => id !== issueId)
        : [...prev, issueId]
    );
  };

  const handleSubmit = (
    ratingValue: number = rating || 3,
    helpful: boolean = (ratingValue >= 4),
    issues: string[] = selectedIssues,
    suggest: string = suggestions
  ) => {
    onSubmit({
      executionId,
      rating: ratingValue,
      wasHelpful: helpful,
      issues: issues.length > 0 ? issues : undefined,
      suggestions: suggest.trim() || undefined,
    });
    setSubmitted(true);
    setTimeout(() => {
      setIsOpen(false);
      setSubmitted(false);
      setRating(null);
      setSelectedIssues([]);
      setSuggestions("");
    }, 2000);
  };

  if (submitted) {
    return (
      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4 flex items-center gap-3 animate-scale-in">
        <div className="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center text-white">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <div className="flex-1">
          <p className="font-medium text-green-900 dark:text-green-100">
            Obrigado pelo feedback!
          </p>
          <p className="text-sm text-green-700 dark:text-green-300">
            Vamos usar para melhorar o {agentName}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl p-4 space-y-4">
      {/* Rating Stars */}
      {!isOpen && (
        <div>
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Como foi a resposta do {agentName}?
          </p>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((value) => (
              <button
                key={value}
                onClick={() => handleRatingClick(value)}
                className="group relative p-2 hover:scale-110 transition-transform"
                title={`${value} ${value === 1 ? "estrela" : "estrelas"}`}
              >
                <svg
                  className={`w-8 h-8 transition-colors ${
                    rating && rating >= value
                      ? "text-yellow-400 fill-yellow-400"
                      : "text-gray-300 dark:text-slate-600 group-hover:text-yellow-300"
                  }`}
                  fill={rating && rating >= value ? "currentColor" : "none"}
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
                  />
                </svg>
                {/* Tooltip */}
                <span className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                  {value === 1 && "Muito ruim"}
                  {value === 2 && "Ruim"}
                  {value === 3 && "Regular"}
                  {value === 4 && "Bom"}
                  {value === 5 && "Excelente"}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Detailed Feedback */}
      {isOpen && rating && rating < 4 && (
        <div className="space-y-4 animate-scale-in">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              O que podemos melhorar?
            </p>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Issue Checkboxes */}
          <div className="grid grid-cols-2 gap-2">
            {feedbackIssues.map((issue) => (
              <button
                key={issue.id}
                onClick={() => toggleIssue(issue.id)}
                className={`flex items-center gap-2 p-3 rounded-xl text-left transition-all ${
                  selectedIssues.includes(issue.id)
                    ? "bg-blue-100 dark:bg-blue-900/30 border-2 border-blue-500 text-blue-700 dark:text-blue-300"
                    : "bg-gray-50 dark:bg-slate-700 border-2 border-transparent text-gray-700 dark:text-gray-300 hover:border-gray-300 dark:hover:border-slate-600"
                }`}
              >
                <span className="text-lg">{issue.icon}</span>
                <span className="text-sm font-medium">{issue.label}</span>
                {selectedIssues.includes(issue.id) && (
                  <svg className="w-4 h-4 ml-auto text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            ))}
          </div>

          {/* Suggestions */}
          <div>
            <label htmlFor="suggestions" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Sugestões (opcional)
            </label>
            <textarea
              id="suggestions"
              value={suggestions}
              onChange={(e) => setSuggestions(e.target.value)}
              placeholder="Como podemos melhorar este agente?"
              rows={3}
              className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
            />
          </div>

          {/* Submit Button */}
          <button
            onClick={() => handleSubmit()}
            className="w-full px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-medium hover:opacity-90 transition-opacity"
          >
            Enviar Feedback
          </button>
        </div>
      )}
    </div>
  );
}
