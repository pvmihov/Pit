import * as readline from 'node:readline/promises';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { inflate, deflate } from 'node:zlib';
import { promisify } from 'node:util';
const doInflate = promisify(inflate);
const doDeflate = promisify(deflate);
import archiver from 'archiver';

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
})

//let root_dir = await rl.question('Enter the path that will be used to store project information:\n')
let root_dir = '/home/petar/images'
do{
  try
  {
    const stats = await fs.stat(root_dir)
    if (stats.isDirectory())
    {
      break;
    }
    else
      {
        console.log('Path isn\'t a directory.')
      }
    }
    catch (err)
    {
      console.log('Couldn\'t open.')
    }
    root_dir = await rl.question('Try again:\n')
}while(true);
root_dir = path.resolve(root_dir)
console.log(`Using ${root_dir} as path.`)
  
async function create_pit(root_dir)
{
  console.log('.pit folder does not exist, so I am creating one.')
  await fs.mkdir(path.join(root_dir,'.pit'));
  await fs.mkdir(path.join(root_dir,'.pit','objects'))
  await fs.mkdir(path.join(root_dir,'.pit','refs','heads'),{recursive:true})
  await fs.writeFile(path.join(root_dir,'.pit','refs','heads','Main'),'-')
}

try
{
  let pit_dir = await fs.stat( path.join(root_dir,'.pit') )
  if (!pit_dir.isDirectory())
  {
    create_pit(root_dir)
  }
  else
  {
    console.log('.pit folder is found, so defaulting project to it.')
  }
}
catch (err)
{
  create_pit(root_dir)
}

//let number = await rl.question('Enter server number between 1024 and 65535:\n')
let number = 6767
number = parseInt(number)
while (isNaN(number) || number<1024 || number>65535)
{
  number = await rl.question('Please enter a number in the range 1024 and 65535:\n')
  number = parseInt(number)
}
rl.close()
console.log(`Using localhost:${number} as server`)

http
  .createServer(async (request, response) => {
    if (request.method === 'GET' && request.url === '/clone')
    {
        response.writeHead(200, {
            'Content-Type': 'application/zip',
            'Content-Disposition': 'attachment; filename="project.zip"'
        })
        const archive = archiver('zip', {
            zlib: { level: 9 }
        })
        archive.on('error', (err) => {
            console.error("Archive error:", err)
            if (!response.headersSent) {
                response.writeHead(500)
            }
            response.end('Failed to generate archive')
        })
        archive.pipe(response)
        archive.directory(path.join(root_dir,'.pit'), '.pit');
        archive.finalize()
    }
    else if (request.method === 'GET' && request.url === '/fetch')
    {
        response.writeHead(200, {
            'Content-Type': 'application/zip',
            'Content-Disposition': 'attachment; filename="project.zip"'
        })
        const archive = archiver('zip', {
            zlib: { level: 9 }
        })
        archive.on('error', (err) => {
            console.error("Archive error:", err)
            if (!response.headersSent) {
                response.writeHead(500)
            }
            response.end('Failed to generate archive')
        })
        archive.pipe(response)
        archive.directory(path.join(root_dir,'.pit', 'objects'), 'objects');
        archive.finalize()
    }
    else if (request.method === 'GET' && request.url === '/pull')
    {
      let cur_branch = request.headers['x-current-branch']
      try {
        const data = await fs.readFile(path.join(root_dir, '.pit', 'refs', 'heads', cur_branch), { encoding: 'utf8' })
        const data_text = data.toString()
        response.writeHead(200,{
          'Content-Type': 'text/plain'
        })
        response.write(data_text)
        response.end()
      } catch (err) {
        if (err.code === 'ENOENT')
        {
          response.statusCode = 204
          response.end()
        }
      }
      response.end()
    }
    else
    {
      response.statusCode = 404
      response.end()
    }
  })
  .listen(number);

