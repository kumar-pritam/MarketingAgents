# Stage 1: Production image only
FROM node:20-slim

WORKDIR /app

COPY . .

ENV NEXT_PUBLIC_API_URL=/api/v1
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

EXPOSE 3000

CMD ["npm", "start"]