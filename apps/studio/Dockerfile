# Frontend Dockerfile
# Multi-stage build for Next.js

# ==================== BUILD ====================
FROM node:20-alpine AS builder
WORKDIR /app

# Copy package files and install ALL dependencies (including dev)
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code
COPY . .

# Build arguments - baked into the build
ARG NEXT_PUBLIC_API_URL=http://localhost:4000
ARG NEXT_PUBLIC_APP_NAME="Agno Multi-Agent Platform"
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_APP_NAME=$NEXT_PUBLIC_APP_NAME

# Build application
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ==================== PRODUCTION ====================
FROM node:20-alpine AS runner
WORKDIR /app

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Set ownership
RUN chown -R nextjs:nodejs /app

USER nextjs

# Environment
ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

EXPOSE 3000

CMD ["node", "server.js"]
