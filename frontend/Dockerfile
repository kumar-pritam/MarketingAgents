FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json* ./

RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps

COPY . .

RUN npm run build

ENV NEXT_PUBLIC_API_URL=/api/v1

EXPOSE 3000

CMD ["npm", "start"]