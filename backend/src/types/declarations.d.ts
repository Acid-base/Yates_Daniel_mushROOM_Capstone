// Type declarations for modules without TypeScript definitions

declare module 'dotenv' {
  export function config(options?: { path?: string }): void;
}

declare module 'bottleneck' {
  interface BottleneckOptions {
    minTime?: number;
    maxConcurrent?: number;
    reservoir?: number;
    reservoirRefreshAmount?: number;
    reservoirRefreshInterval?: number;
  }

  class Bottleneck {
    constructor(options?: BottleneckOptions);
    schedule<T>(fn: () => Promise<T>): Promise<T>;
  }

  export default Bottleneck;
}

declare module 'mongodb' {
  export class MongoClient {
    static connect(url: string): Promise<MongoClient>;
    db(name: string): Db;
    close(): Promise<void>;
  }

  export class Db {
    collection<T = any>(name: string): Collection<T>;
  }

  export class Collection<T = any> {
    find(query?: any): FindCursor<T>;
    findOne(query?: any): Promise<T | null>;
    insertOne(doc: any): Promise<any>;
    updateOne(filter: any, update: any): Promise<any>;
    deleteOne(filter: any): Promise<any>;
    distinct(field: string, query?: any): Promise<any[]>;
    countDocuments(query?: any): Promise<number>;
    aggregate(pipeline: any[]): AggregationCursor<any>;
  }

  export class FindCursor<T = any> {
    toArray(): Promise<T[]>;
    limit(n: number): FindCursor<T>;
    skip(n: number): FindCursor<T>;
    sort(sort: any): FindCursor<T>;
  }

  export class AggregationCursor<T = any> {
    toArray(): Promise<T[]>;
  }

  export class ObjectId {
    constructor(id?: string);
    toString(): string;
    static isValid(id: string): boolean;
  }
}

declare module '@aws-sdk/client-s3' {
  export class S3Client {
    constructor(config: any);
    send(command: any): Promise<any>;
  }

  export class GetObjectCommand {
    constructor(params: any);
  }

  export class PutObjectCommand {
    constructor(params: any);
  }
}

declare module '@aws-sdk/s3-request-presigner' {
  export function getSignedUrl(client: any, command: any, options?: any): Promise<string>;
}
