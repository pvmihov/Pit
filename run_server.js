import * as readline from 'node:readline/promises';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { inflate, deflate } from 'node:zlib';
import { promisify } from 'node:util';
const doInflate = promisify(inflate);
const doDeflate = promisify(deflate);

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
})

let root_dir = await rl.question('Enter the path that will be used to store project information:\n')
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
  await fs.writeFile(path.join(root_dir,'.pit','HEAD'),'Main')
  await fs.writeFile(path.join(root_dir,'.pit','refs','heads','Main'),'-')
  const index_content = '0\x1e0\x1e'
  const index_compr = await doDeflate(index_content)
  await fs.writeFile(path.join(root_dir,'.pit','index'),index_compr)
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

/*
let number = await rl.question('Enter server number between 1024 and 65535:\n')
number = parseInt(number)
while (isNaN(number) || number<1024 || number>65535)
{
  number = await rl.question('Please enter a number in the range 1024 and 65535:\n')
  number = parseInt(number)
}
console.log(`Using localhost:${number} as server`)

http
  .createServer((request, response) => {

  })
  .listen(number);
*/

rl.close()
