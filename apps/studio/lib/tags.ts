// Sistema de Tags/Labels para Agents e Teams

const STORAGE_KEY = "agno_tags";

export interface TagsData {
  agents: Record<string, string[]>;
  teams: Record<string, string[]>;
  availableTags: string[];
}

const DEFAULT_TAGS = ["produção", "desenvolvimento", "teste", "importante", "arquivado"];

const getDefaultData = (): TagsData => ({
  agents: {},
  teams: {},
  availableTags: DEFAULT_TAGS,
});

export const getTagsData = (): TagsData => {
  if (typeof window === "undefined") return getDefaultData();
  
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return getDefaultData();
    const data = JSON.parse(stored);
    return {
      ...getDefaultData(),
      ...data,
    };
  } catch {
    return getDefaultData();
  }
};

export const saveTagsData = (data: TagsData): void => {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
};

// Agent Tags
export const getAgentTags = (name: string): string[] => {
  const data = getTagsData();
  return data.agents[name] || [];
};

export const setAgentTags = (name: string, tags: string[]): void => {
  const data = getTagsData();
  if (tags.length > 0) {
    data.agents[name] = tags;
  } else {
    delete data.agents[name];
  }
  saveTagsData(data);
};

export const addAgentTag = (name: string, tag: string): void => {
  const tags = getAgentTags(name);
  if (!tags.includes(tag)) {
    setAgentTags(name, [...tags, tag]);
  }
};

export const removeAgentTag = (name: string, tag: string): void => {
  const tags = getAgentTags(name);
  setAgentTags(name, tags.filter(t => t !== tag));
};

// Team Tags
export const getTeamTags = (name: string): string[] => {
  const data = getTagsData();
  return data.teams[name] || [];
};

export const setTeamTags = (name: string, tags: string[]): void => {
  const data = getTagsData();
  if (tags.length > 0) {
    data.teams[name] = tags;
  } else {
    delete data.teams[name];
  }
  saveTagsData(data);
};

// Available Tags
export const getAvailableTags = (): string[] => {
  return getTagsData().availableTags;
};

export const addAvailableTag = (tag: string): void => {
  const data = getTagsData();
  if (!data.availableTags.includes(tag)) {
    data.availableTags.push(tag);
    saveTagsData(data);
  }
};

// Tag colors
export const TAG_COLORS: Record<string, string> = {
  "produção": "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  "desenvolvimento": "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  "teste": "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  "importante": "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  "arquivado": "bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400",
};

export const getTagColor = (tag: string): string => {
  return TAG_COLORS[tag] || "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400";
};
