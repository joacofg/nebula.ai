FROM node:22-alpine AS deps
WORKDIR /app/console
COPY console/package*.json ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app/console
COPY --from=deps /app/console/node_modules ./node_modules
COPY console ./
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app/console
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000
COPY --from=builder /app/console/.next/standalone ./
COPY --from=builder /app/console/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
